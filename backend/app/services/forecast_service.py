from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.models import (
    Forecast, Budget, Actual, CostCenter, Account, ForecastMethod,
)

MONTH_COLS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def generate_forecast(
    db: Session,
    version_id: UUID,
    year: int,
    method: str,
    user_id: UUID,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
) -> dict:
    budget_query = db.query(Budget).filter(Budget.version_id == version_id)
    if cost_center_id:
        budget_query = budget_query.filter(Budget.cost_center_id == cost_center_id)
    if account_id:
        budget_query = budget_query.filter(Budget.account_id == account_id)
    budgets = budget_query.all()

    if not budgets:
        return {"created": 0, "message": "No budget rows found for the given filters"}

    cost_center_ids = list({b.cost_center_id for b in budgets})
    account_ids = list({b.account_id for b in budgets})

    current_month = datetime.utcnow().month

    actual_query = db.query(
        Actual.cost_center_id,
        Actual.account_id,
        extract("month", Actual.date).label("month"),
        func.sum(Actual.amount).label("total"),
    ).filter(
        extract("year", Actual.date) == year,
        Actual.cost_center_id.in_(cost_center_ids),
        Actual.account_id.in_(account_ids),
    ).group_by(
        Actual.cost_center_id, Actual.account_id, extract("month", Actual.date)
    )

    actuals_map = {}
    for row in actual_query.all():
        key = (row.cost_center_id, row.account_id)
        if key not in actuals_map:
            actuals_map[key] = {}
        actuals_map[key][int(row.month)] = Decimal(str(row.total))

    prev_year_actuals_map = {}
    if method == "historical":
        prev_actual_query = db.query(
            Actual.cost_center_id,
            Actual.account_id,
            extract("month", Actual.date).label("month"),
            func.sum(Actual.amount).label("total"),
        ).filter(
            extract("year", Actual.date) == year - 1,
            Actual.cost_center_id.in_(cost_center_ids),
            Actual.account_id.in_(account_ids),
        ).group_by(
            Actual.cost_center_id, Actual.account_id, extract("month", Actual.date)
        )
        for row in prev_actual_query.all():
            key = (row.cost_center_id, row.account_id)
            if key not in prev_year_actuals_map:
                prev_year_actuals_map[key] = {}
            prev_year_actuals_map[key][int(row.month)] = Decimal(str(row.total))

    created = 0
    for budget in budgets:
        key = (budget.cost_center_id, budget.account_id)
        actuals_for_key = actuals_map.get(key, {})

        months = {}
        for m_idx, col in enumerate(MONTH_COLS, 1):
            if m_idx <= current_month and m_idx in actuals_for_key:
                months[col] = actuals_for_key[m_idx]
            else:
                if method == "linear":
                    months[col] = _forecast_linear(actuals_for_key, current_month, budget, col)
                elif method == "historical":
                    prev_actuals = prev_year_actuals_map.get(key, {})
                    months[col] = _forecast_historical(actuals_for_key, current_month, prev_actuals, m_idx, budget, col)
                else:
                    months[col] = getattr(budget, col) or Decimal("0")

        total = sum(months.values())

        existing = db.query(Forecast).filter(
            Forecast.version_id == version_id,
            Forecast.cost_center_id == budget.cost_center_id,
            Forecast.account_id == budget.account_id,
        ).first()

        if existing:
            for col in MONTH_COLS:
                setattr(existing, col, months[col])
            existing.total = total
            existing.method = ForecastMethod(method)
            existing.generated_at = datetime.utcnow()
        else:
            forecast = Forecast(
                version_id=version_id,
                cost_center_id=budget.cost_center_id,
                account_id=budget.account_id,
                total=total,
                method=ForecastMethod(method),
                created_by=user_id,
                **months,
            )
            db.add(forecast)
        created += 1

    db.commit()
    return {"created": created, "method": method, "year": year}


def _forecast_linear(actuals: dict, current_month: int, budget, col: str) -> Decimal:
    actual_values = [actuals.get(m, Decimal("0")) for m in range(1, current_month + 1) if m in actuals]
    if actual_values:
        avg = sum(actual_values) / len(actual_values)
        return Decimal(str(round(float(avg), 2)))
    return getattr(budget, col) or Decimal("0")


def _forecast_historical(actuals: dict, current_month: int, prev_actuals: dict, month_idx: int, budget, col: str) -> Decimal:
    if month_idx in prev_actuals:
        return prev_actuals[month_idx]
    return getattr(budget, col) or Decimal("0")
