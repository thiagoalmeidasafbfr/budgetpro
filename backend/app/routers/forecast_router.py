from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Forecast, BudgetVersion, VersionStatus
from app.schemas.schemas import ForecastCreate, ForecastResponse, ForecastGenerate
from app.auth.auth import get_current_user, require_role
from app.services.forecast_service import generate_forecast

router = APIRouter(prefix="/api/forecasts", tags=["Forecasts"])


@router.get("/", response_model=List[ForecastResponse])
def list_forecasts(
    version_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Forecast)
    if version_id:
        query = query.filter(Forecast.version_id == version_id)
    if cost_center_id:
        query = query.filter(Forecast.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Forecast.account_id == account_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.post("/", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    data: ForecastCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == data.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")

    months_vals = [data.jan, data.feb, data.mar, data.apr, data.may, data.jun,
                   data.jul, data.aug, data.sep, data.oct, data.nov, data.dec]
    total = sum(v or 0 for v in months_vals)

    forecast = Forecast(
        version_id=data.version_id,
        cost_center_id=data.cost_center_id,
        account_id=data.account_id,
        jan=data.jan, feb=data.feb, mar=data.mar,
        apr=data.apr, may=data.may, jun=data.jun,
        jul=data.jul, aug=data.aug, sep=data.sep,
        oct=data.oct, nov=data.nov, dec=data.dec,
        total=total,
        method=data.method,
        created_by=current_user.id,
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


@router.post("/generate", response_model=dict)
def generate_forecasts(
    data: ForecastGenerate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == data.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")

    result = generate_forecast(
        db=db,
        version_id=data.version_id,
        year=data.year,
        method=data.method.value,
        user_id=current_user.id,
        cost_center_id=data.cost_center_id,
        account_id=data.account_id,
    )
    return result


@router.put("/{forecast_id}", response_model=ForecastResponse)
def update_forecast(
    forecast_id: UUID,
    data: ForecastCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    forecast.version_id = data.version_id
    forecast.cost_center_id = data.cost_center_id
    forecast.account_id = data.account_id
    forecast.jan = data.jan
    forecast.feb = data.feb
    forecast.mar = data.mar
    forecast.apr = data.apr
    forecast.may = data.may
    forecast.jun = data.jun
    forecast.jul = data.jul
    forecast.aug = data.aug
    forecast.sep = data.sep
    forecast.oct = data.oct
    forecast.nov = data.nov
    forecast.dec = data.dec
    forecast.method = data.method

    months_vals = [data.jan, data.feb, data.mar, data.apr, data.may, data.jun,
                   data.jul, data.aug, data.sep, data.oct, data.nov, data.dec]
    forecast.total = sum(v or 0 for v in months_vals)

    db.commit()
    db.refresh(forecast)
    return forecast


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    db.delete(forecast)
    db.commit()
