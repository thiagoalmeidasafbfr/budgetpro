from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth.auth import get_current_user
from app.services.dashboard_service import (
    get_kpis, get_budget_vs_actual_chart, get_cumulative_chart,
    get_burn_rate_chart, get_top_cost_centers, get_top_expenses,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis")
def dashboard_kpis(
    year: int = Query(2026),
    centro_de_custo_id: Optional[UUID] = None,
    conta_contabil_id: Optional[UUID] = None,
    departamento_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_kpis(db, year, centro_de_custo_id, conta_contabil_id, departamento_id)


@router.get("/charts/budget-vs-actual")
def chart_budget_vs_actual(
    year: int = Query(2026),
    centro_de_custo_id: Optional[UUID] = None,
    departamento_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_budget_vs_actual_chart(db, year, centro_de_custo_id, departamento_id)


@router.get("/charts/cumulative")
def chart_cumulative(
    year: int = Query(2026),
    centro_de_custo_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_cumulative_chart(db, year, centro_de_custo_id)


@router.get("/charts/burn-rate")
def chart_burn_rate(
    year: int = Query(2026),
    centro_de_custo_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_burn_rate_chart(db, year, centro_de_custo_id)


@router.get("/charts/top-cost-centers")
def chart_top_cost_centers(
    year: int = Query(2026),
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_top_cost_centers(db, year, top_n)


@router.get("/charts/top-expenses")
def chart_top_expenses(
    year: int = Query(2026),
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_top_expenses(db, year, top_n)
