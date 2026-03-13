from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from app.models.models import (
    Budget, Actual, Forecast, CostCenter, Account, BudgetVersion, Department,
    VersionStatus,
)
from app.schemas.schemas import (
    DashboardKPIs, MonthlyData, CumulativeData, BurnRateData, TopItem,
)

MONTHS = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr",
    5: "may", 6: "jun", 7: "jul", 8: "aug",
    9: "sep", 10: "oct", 11: "nov", 12: "dec",
}

MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _resolve_version(db: Session, year: int, version_id: Optional[UUID] = None) -> Optional[BudgetVersion]:
    """Find the budget version to use for queries."""
    if version_id:
        return db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    return (
        db.query(BudgetVersion)
        .filter(BudgetVersion.year == year, BudgetVersion.status == VersionStatus.approved)
        .order_by(BudgetVersion.created_at.asc())
        .first()
    )


def _apply_budget_filters(query, department_id=None, cost_center_id=None, account_id=None):
    """Apply common filters to a budget/forecast query."""
    if cost_center_id:
        query = query.filter(Budget.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Budget.account_id == account_id)
    if department_id:
        query = query.join(CostCenter, Budget.cost_center_id == CostCenter.id).filter(
            CostCenter.department_id == department_id
        )
    return query


def _apply_forecast_filters(query, department_id=None, cost_center_id=None, account_id=None):
    """Apply common filters to a forecast query."""
    if cost_center_id:
        query = query.filter(Forecast.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Forecast.account_id == account_id)
    if department_id:
        query = query.join(CostCenter, Forecast.cost_center_id == CostCenter.id).filter(
            CostCenter.department_id == department_id
        )
    return query


def _apply_actual_filters(query, year: int, department_id=None, cost_center_id=None, account_id=None):
    """Apply common filters to an actuals query."""
    query = query.filter(extract("year", Actual.date) == year)
    if cost_center_id:
        query = query.filter(Actual.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Actual.account_id == account_id)
    if department_id:
        query = query.join(CostCenter, Actual.cost_center_id == CostCenter.id).filter(
            CostCenter.department_id == department_id
        )
    return query


def get_kpis(
    db: Session,
    year: int,
    version_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
) -> DashboardKPIs:
    version = _resolve_version(db, year, version_id)

    total_budget = Decimal("0")
    total_forecast = Decimal("0")

    if version:
        # Sum budget totals
        budget_q = db.query(func.coalesce(func.sum(Budget.total), 0)).filter(
            Budget.version_id == version.id
        )
        budget_q = _apply_budget_filters(budget_q, department_id, cost_center_id, account_id)
        total_budget = Decimal(str(budget_q.scalar() or 0))

        # Sum forecast totals
        forecast_q = db.query(func.coalesce(func.sum(Forecast.total), 0)).filter(
            Forecast.version_id == version.id
        )
        forecast_q = _apply_forecast_filters(forecast_q, department_id, cost_center_id, account_id)
        total_forecast = Decimal(str(forecast_q.scalar() or 0))

    # Sum actuals
    actual_q = db.query(func.coalesce(func.sum(Actual.amount), 0))
    actual_q = _apply_actual_filters(actual_q, year, department_id, cost_center_id, account_id)
    total_actual = Decimal(str(actual_q.scalar() or 0))

    variance = total_budget - total_actual
    variance_pct = None
    budget_utilization_pct = None
    if total_budget != 0:
        variance_pct = round(float(variance / total_budget * 100), 2)
        budget_utilization_pct = round(float(total_actual / total_budget * 100), 2)

    return DashboardKPIs(
        total_budget=total_budget,
        total_actual=total_actual,
        total_forecast=total_forecast,
        variance=variance,
        variance_pct=variance_pct,
        budget_utilization_pct=budget_utilization_pct,
    )


def get_budget_vs_actual_chart(
    db: Session,
    year: int,
    version_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
) -> List[MonthlyData]:
    version = _resolve_version(db, year, version_id)

    # Build per-month budget sums from budget columns
    budget_by_month = {}
    if version:
        budget_q = db.query(Budget).filter(Budget.version_id == version.id)
        budget_q = _apply_budget_filters(budget_q, department_id, cost_center_id, account_id)
        budgets = budget_q.all()

        for month_num, col_name in MONTHS.items():
            total = sum(getattr(b, col_name) or Decimal("0") for b in budgets)
            budget_by_month[month_num] = total
    else:
        for month_num in range(1, 13):
            budget_by_month[month_num] = Decimal("0")

    # Build per-month actual sums
    actual_base = db.query(
        extract("month", Actual.date).label("month"),
        func.sum(Actual.amount).label("total"),
    )
    actual_base = _apply_actual_filters(actual_base, year, department_id, cost_center_id, account_id)
    actual_rows = actual_base.group_by(extract("month", Actual.date)).all()

    actual_by_month = {int(row.month): Decimal(str(row.total)) for row in actual_rows}

    result = []
    for month_num in range(1, 13):
        result.append(MonthlyData(
            month=MONTH_LABELS[month_num - 1],
            budget=budget_by_month.get(month_num, Decimal("0")),
            actual=actual_by_month.get(month_num, Decimal("0")),
        ))
    return result


def get_cumulative_chart(
    db: Session,
    year: int,
    version_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
) -> List[CumulativeData]:
    version = _resolve_version(db, year, version_id)

    # Budget per month
    budget_by_month = {}
    if version:
        budget_q = db.query(Budget).filter(Budget.version_id == version.id)
        if cost_center_id:
            budget_q = budget_q.filter(Budget.cost_center_id == cost_center_id)
        budgets = budget_q.all()

        for month_num, col_name in MONTHS.items():
            total = sum(getattr(b, col_name) or Decimal("0") for b in budgets)
            budget_by_month[month_num] = total
    else:
        for month_num in range(1, 13):
            budget_by_month[month_num] = Decimal("0")

    # Actuals per month
    actual_base = db.query(
        extract("month", Actual.date).label("month"),
        func.sum(Actual.amount).label("total"),
    ).filter(extract("year", Actual.date) == year)
    if cost_center_id:
        actual_base = actual_base.filter(Actual.cost_center_id == cost_center_id)
    actual_rows = actual_base.group_by(extract("month", Actual.date)).all()
    actual_by_month = {int(row.month): Decimal(str(row.total)) for row in actual_rows}

    result = []
    cum_actual = Decimal("0")
    cum_budget = Decimal("0")
    for month_num in range(1, 13):
        cum_actual += actual_by_month.get(month_num, Decimal("0"))
        cum_budget += budget_by_month.get(month_num, Decimal("0"))
        result.append(CumulativeData(
            month=MONTH_LABELS[month_num - 1],
            cumulative_actual=cum_actual,
            cumulative_budget=cum_budget,
        ))
    return result


def get_burn_rate_chart(
    db: Session,
    year: int,
    version_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
) -> List[BurnRateData]:
    version = _resolve_version(db, year, version_id)

    # Total annual budget
    total_budget = Decimal("0")
    if version:
        budget_q = db.query(func.coalesce(func.sum(Budget.total), 0)).filter(
            Budget.version_id == version.id
        )
        if cost_center_id:
            budget_q = budget_q.filter(Budget.cost_center_id == cost_center_id)
        total_budget = Decimal(str(budget_q.scalar() or 0))

    # Actuals per month
    actual_base = db.query(
        extract("month", Actual.date).label("month"),
        func.sum(Actual.amount).label("total"),
    ).filter(extract("year", Actual.date) == year)
    if cost_center_id:
        actual_base = actual_base.filter(Actual.cost_center_id == cost_center_id)
    actual_rows = actual_base.group_by(extract("month", Actual.date)).all()
    actual_by_month = {int(row.month): Decimal(str(row.total)) for row in actual_rows}

    result = []
    cumulative_spend = Decimal("0")
    months_with_data = 0
    for month_num in range(1, 13):
        monthly_spend = actual_by_month.get(month_num, Decimal("0"))
        cumulative_spend += monthly_spend
        if monthly_spend > 0:
            months_with_data += 1
        avg_monthly = (cumulative_spend / months_with_data) if months_with_data > 0 else Decimal("0")
        remaining = total_budget - cumulative_spend

        result.append(BurnRateData(
            month=MONTH_LABELS[month_num - 1],
            monthly_spend=monthly_spend,
            avg_monthly_spend=Decimal(str(round(float(avg_monthly), 2))),
            remaining_budget=remaining,
        ))
    return result


def get_top_cost_centers(
    db: Session,
    year: int,
    top_n: int = 10,
) -> List[TopItem]:
    rows = (
        db.query(
            CostCenter.name,
            CostCenter.code,
            func.sum(Actual.amount).label("total"),
        )
        .join(CostCenter, Actual.cost_center_id == CostCenter.id)
        .filter(extract("year", Actual.date) == year)
        .group_by(CostCenter.name, CostCenter.code)
        .order_by(func.sum(Actual.amount).desc())
        .limit(top_n)
        .all()
    )

    # Calculate grand total for percentages
    grand_total_row = (
        db.query(func.sum(Actual.amount))
        .filter(extract("year", Actual.date) == year)
        .scalar()
    )
    grand_total = Decimal(str(grand_total_row or 0))

    result = []
    for row in rows:
        amount = Decimal(str(row.total))
        pct = round(float(amount / grand_total * 100), 2) if grand_total > 0 else 0.0
        result.append(TopItem(
            name=row.name,
            code=row.code,
            amount=amount,
            percentage=pct,
        ))
    return result


def get_top_expenses(
    db: Session,
    year: int,
    top_n: int = 10,
) -> List[TopItem]:
    rows = (
        db.query(
            Account.name,
            Account.code,
            func.sum(Actual.amount).label("total"),
        )
        .join(Account, Actual.account_id == Account.id)
        .filter(extract("year", Actual.date) == year)
        .group_by(Account.name, Account.code)
        .order_by(func.sum(Actual.amount).desc())
        .limit(top_n)
        .all()
    )

    grand_total_row = (
        db.query(func.sum(Actual.amount))
        .filter(extract("year", Actual.date) == year)
        .scalar()
    )
    grand_total = Decimal(str(grand_total_row or 0))

    result = []
    for row in rows:
        amount = Decimal(str(row.total))
        pct = round(float(amount / grand_total * 100), 2) if grand_total > 0 else 0.0
        result.append(TopItem(
            name=row.name,
            code=row.code,
            amount=amount,
            percentage=pct,
        ))
    return result
