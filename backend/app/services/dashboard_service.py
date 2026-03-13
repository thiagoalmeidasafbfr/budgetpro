from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.models import (
    Lancamento, CentroDeCusto, ContaContabil,
)
from app.schemas.schemas import (
    DashboardKPIs, MonthlyData, CumulativeData, BurnRateData, TopItem,
)

MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

FONTE_BUDGET = "Budget"
FONTE_RAZAO = "Razão"


def _sum_lancamentos(
    db: Session, year: int, fonte: str,
    centro_de_custo_id=None, conta_contabil_id=None, departamento_id=None,
) -> Decimal:
    q = db.query(func.coalesce(func.sum(Lancamento.valor), 0)).filter(
        extract("year", Lancamento.data_lancamento) == year,
        Lancamento.fonte == fonte,
    )
    if centro_de_custo_id:
        q = q.filter(Lancamento.centro_de_custo_id == str(centro_de_custo_id))
    if conta_contabil_id:
        q = q.filter(Lancamento.conta_contabil_id == str(conta_contabil_id))
    if departamento_id:
        q = q.join(CentroDeCusto, Lancamento.centro_de_custo_id == CentroDeCusto.id).filter(
            CentroDeCusto.departamento_id == str(departamento_id)
        )
    return Decimal(str(q.scalar() or 0))


def get_kpis(
    db: Session, year: int,
    centro_de_custo_id=None, conta_contabil_id=None, departamento_id=None,
) -> DashboardKPIs:
    total_budget = _sum_lancamentos(db, year, FONTE_BUDGET, centro_de_custo_id, conta_contabil_id, departamento_id)
    total_actual = _sum_lancamentos(db, year, FONTE_RAZAO, centro_de_custo_id, conta_contabil_id, departamento_id)
    total_forecast = Decimal("0")
    variance = total_budget - total_actual
    variance_pct = round(float(variance / total_budget * 100), 2) if total_budget != 0 else None
    budget_utilization_pct = round(float(total_actual / total_budget * 100), 2) if total_budget != 0 else None
    return DashboardKPIs(
        total_budget=total_budget, total_actual=total_actual,
        total_forecast=total_forecast, variance=variance,
        variance_pct=variance_pct, budget_utilization_pct=budget_utilization_pct,
    )


def _monthly_sums(db: Session, year: int, fonte: str, centro_de_custo_id=None, departamento_id=None) -> dict:
    q = db.query(
        extract("month", Lancamento.data_lancamento).label("month"),
        func.sum(Lancamento.valor).label("total"),
    ).filter(
        extract("year", Lancamento.data_lancamento) == year,
        Lancamento.fonte == fonte,
    )
    if centro_de_custo_id:
        q = q.filter(Lancamento.centro_de_custo_id == str(centro_de_custo_id))
    if departamento_id:
        q = q.join(CentroDeCusto, Lancamento.centro_de_custo_id == CentroDeCusto.id).filter(
            CentroDeCusto.departamento_id == str(departamento_id)
        )
    rows = q.group_by(extract("month", Lancamento.data_lancamento)).all()
    return {int(r.month): Decimal(str(r.total)) for r in rows}


def get_budget_vs_actual_chart(db: Session, year: int, centro_de_custo_id=None, departamento_id=None) -> List[MonthlyData]:
    budget_by_month = _monthly_sums(db, year, FONTE_BUDGET, centro_de_custo_id, departamento_id)
    actual_by_month = _monthly_sums(db, year, FONTE_RAZAO, centro_de_custo_id, departamento_id)
    return [
        MonthlyData(
            month=MONTH_LABELS[m - 1],
            budget=budget_by_month.get(m, Decimal("0")),
            actual=actual_by_month.get(m, Decimal("0")),
        )
        for m in range(1, 13)
    ]


def get_cumulative_chart(db: Session, year: int, centro_de_custo_id=None) -> List[CumulativeData]:
    budget_by_month = _monthly_sums(db, year, FONTE_BUDGET, centro_de_custo_id)
    actual_by_month = _monthly_sums(db, year, FONTE_RAZAO, centro_de_custo_id)
    result, cum_budget, cum_actual = [], Decimal("0"), Decimal("0")
    for m in range(1, 13):
        cum_budget += budget_by_month.get(m, Decimal("0"))
        cum_actual += actual_by_month.get(m, Decimal("0"))
        result.append(CumulativeData(month=MONTH_LABELS[m - 1], cumulative_budget=cum_budget, cumulative_actual=cum_actual))
    return result


def get_burn_rate_chart(db: Session, year: int, centro_de_custo_id=None) -> List[BurnRateData]:
    total_budget = _sum_lancamentos(db, year, FONTE_BUDGET, centro_de_custo_id)
    actual_by_month = _monthly_sums(db, year, FONTE_RAZAO, centro_de_custo_id)
    result, cumulative_spend, months_with_data = [], Decimal("0"), 0
    for m in range(1, 13):
        monthly_spend = actual_by_month.get(m, Decimal("0"))
        cumulative_spend += monthly_spend
        if monthly_spend > 0:
            months_with_data += 1
        avg_monthly = (cumulative_spend / months_with_data) if months_with_data > 0 else Decimal("0")
        result.append(BurnRateData(
            month=MONTH_LABELS[m - 1], monthly_spend=monthly_spend,
            avg_monthly_spend=Decimal(str(round(float(avg_monthly), 2))),
            remaining_budget=total_budget - cumulative_spend,
        ))
    return result


def get_top_cost_centers(db: Session, year: int, top_n: int = 10) -> List[TopItem]:
    rows = (
        db.query(CentroDeCusto.nome, CentroDeCusto.codigo, func.sum(Lancamento.valor).label("total"))
        .join(CentroDeCusto, Lancamento.centro_de_custo_id == CentroDeCusto.id)
        .filter(extract("year", Lancamento.data_lancamento) == year, Lancamento.fonte == FONTE_RAZAO)
        .group_by(CentroDeCusto.nome, CentroDeCusto.codigo)
        .order_by(func.sum(Lancamento.valor).desc()).limit(top_n).all()
    )
    grand_total = _sum_lancamentos(db, year, FONTE_RAZAO)
    return [
        TopItem(name=r.nome, code=r.codigo, amount=Decimal(str(r.total)),
                percentage=round(float(Decimal(str(r.total)) / grand_total * 100), 2) if grand_total > 0 else 0.0)
        for r in rows
    ]


def get_top_expenses(db: Session, year: int, top_n: int = 10) -> List[TopItem]:
    rows = (
        db.query(ContaContabil.nome, ContaContabil.numero, func.sum(Lancamento.valor).label("total"))
        .join(ContaContabil, Lancamento.conta_contabil_id == ContaContabil.id)
        .filter(extract("year", Lancamento.data_lancamento) == year, Lancamento.fonte == FONTE_RAZAO)
        .group_by(ContaContabil.nome, ContaContabil.numero)
        .order_by(func.sum(Lancamento.valor).desc()).limit(top_n).all()
    )
    grand_total = _sum_lancamentos(db, year, FONTE_RAZAO)
    return [
        TopItem(name=r.nome, code=r.numero, amount=Decimal(str(r.total)),
                percentage=round(float(Decimal(str(r.total)) / grand_total * 100), 2) if grand_total > 0 else 0.0)
        for r in rows
    ]
