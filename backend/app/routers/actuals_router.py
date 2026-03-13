from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional

from app.database import get_db
from app.models.models import Actual, Budget, BudgetVersion, CostCenter, Account, AccountCategory
from app.schemas.schemas import ActualCreate, ActualResponse, ActualImport
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/actuals", tags=["Actuals"])

MONTH_COLS = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may", 6: "jun",
    7: "jul", 8: "aug", 9: "sep", 10: "oct", 11: "nov", 12: "dec",
}


@router.get("/", response_model=List[ActualResponse])
def list_actuals(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Actual)
    if date_from:
        query = query.filter(Actual.date >= date_from)
    if date_to:
        query = query.filter(Actual.date <= date_to)
    if cost_center_id:
        query = query.filter(Actual.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Actual.account_id == account_id)
    return query.order_by(Actual.date.desc()).offset(skip).limit(limit).all()


@router.get("/{actual_id}", response_model=ActualResponse)
def get_actual(
    actual_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=404, detail="Actual not found")
    return actual


@router.post("/", response_model=ActualResponse, status_code=status.HTTP_201_CREATED)
def create_actual(
    data: ActualCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    actual = Actual(
        date=data.date,
        account_id=data.account_id,
        cost_center_id=data.cost_center_id,
        vendor=data.vendor,
        amount=data.amount,
        description=data.description,
        source=data.source,
    )
    db.add(actual)
    db.commit()
    db.refresh(actual)
    return actual


@router.post("/import", response_model=dict)
def import_actuals(
    data: ActualImport,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    created = 0
    errors = []
    for idx, item in enumerate(data.items):
        try:
            actual = Actual(
                date=item.date,
                account_id=item.account_id,
                cost_center_id=item.cost_center_id,
                vendor=item.vendor,
                amount=item.amount,
                description=item.description,
                source=item.source,
            )
            db.add(actual)
            created += 1
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    db.commit()
    return {"created": created, "errors": errors, "total": len(data.items)}


@router.put("/{actual_id}", response_model=ActualResponse)
def update_actual(
    actual_id: UUID,
    data: ActualCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=404, detail="Actual not found")
    actual.date = data.date
    actual.account_id = data.account_id
    actual.cost_center_id = data.cost_center_id
    actual.vendor = data.vendor
    actual.amount = data.amount
    actual.description = data.description
    actual.source = data.source
    db.commit()
    db.refresh(actual)
    return actual


@router.delete("/{actual_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_actual(
    actual_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    actual = db.query(Actual).filter(Actual.id == actual_id).first()
    if not actual:
        raise HTTPException(status_code=404, detail="Actual not found")
    db.delete(actual)
    db.commit()


@router.get("/vs-budget/{version_id}")
def actuals_vs_budget(
    version_id: UUID,
    year: Optional[int] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")

    target_year = year or version.year

    budget_query = db.query(Budget).filter(Budget.version_id == version_id)
    if cost_center_id:
        budget_query = budget_query.filter(Budget.cost_center_id == cost_center_id)
    if account_id:
        budget_query = budget_query.filter(Budget.account_id == account_id)
    budgets = budget_query.all()

    actual_query = db.query(
        Actual.cost_center_id,
        Actual.account_id,
        extract("month", Actual.date).label("month"),
        func.sum(Actual.amount).label("total"),
    ).filter(
        extract("year", Actual.date) == target_year
    ).group_by(
        Actual.cost_center_id, Actual.account_id, extract("month", Actual.date)
    )
    if cost_center_id:
        actual_query = actual_query.filter(Actual.cost_center_id == cost_center_id)
    if account_id:
        actual_query = actual_query.filter(Actual.account_id == account_id)

    actual_data = {}
    for row in actual_query.all():
        key = (str(row.cost_center_id), str(row.account_id))
        if key not in actual_data:
            actual_data[key] = {}
        actual_data[key][int(row.month)] = float(row.total)

    comparison = []
    for b in budgets:
        key = (str(b.cost_center_id), str(b.account_id))
        actuals_for_key = actual_data.get(key, {})

        months_data = []
        for m in range(1, 13):
            col = MONTH_COLS[m]
            budget_val = float(getattr(b, col) or 0)
            actual_val = actuals_for_key.get(m, 0.0)
            variance = actual_val - budget_val
            months_data.append({
                "month": col,
                "budget": budget_val,
                "actual": actual_val,
                "variance": variance,
                "variance_pct": round((variance / budget_val * 100), 2) if budget_val != 0 else 0.0,
            })

        total_budget = float(b.total or 0)
        total_actual = sum(actuals_for_key.values())
        comparison.append({
            "cost_center_id": str(b.cost_center_id),
            "account_id": str(b.account_id),
            "months": months_data,
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_variance": total_actual - total_budget,
        })

    return {"version_id": str(version_id), "year": target_year, "rows": comparison}
