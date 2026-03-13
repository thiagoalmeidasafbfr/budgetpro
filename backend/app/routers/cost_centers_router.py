from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.models import CostCenter, Department, User
from app.schemas.schemas import CostCenterCreate, CostCenterResponse
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/cost-centers", tags=["Cost Centers"])


def enrich_cost_center(cc: CostCenter) -> dict:
    return {
        "id": cc.id,
        "code": cc.code,
        "name": cc.name,
        "department_id": cc.department_id,
        "responsible_user_id": cc.responsible_user_id,
        "budget_limit": cc.budget_limit,
        "created_at": cc.created_at,
        "department_name": cc.department.name if cc.department else None,
        "responsible_name": cc.responsible_user.name if cc.responsible_user else None,
    }


@router.get("/", response_model=List[CostCenterResponse])
def list_cost_centers(
    department_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(CostCenter).options(
        joinedload(CostCenter.department),
        joinedload(CostCenter.responsible_user),
    )
    if department_id:
        query = query.filter(CostCenter.department_id == department_id)
    centers = query.offset(skip).limit(limit).all()
    return [enrich_cost_center(cc) for cc in centers]


@router.get("/{cc_id}", response_model=CostCenterResponse)
def get_cost_center(
    cc_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cc = db.query(CostCenter).options(
        joinedload(CostCenter.department),
        joinedload(CostCenter.responsible_user),
    ).filter(CostCenter.id == cc_id).first()
    if not cc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")
    return enrich_cost_center(cc)


@router.post("/", response_model=CostCenterResponse, status_code=status.HTTP_201_CREATED)
def create_cost_center(
    data: CostCenterCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    existing = db.query(CostCenter).filter(CostCenter.code == data.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cost center code already exists")
    cc = CostCenter(
        code=data.code,
        name=data.name,
        department_id=data.department_id,
        responsible_user_id=data.responsible_user_id,
        budget_limit=data.budget_limit,
    )
    db.add(cc)
    db.commit()
    db.refresh(cc)
    cc = db.query(CostCenter).options(
        joinedload(CostCenter.department),
        joinedload(CostCenter.responsible_user),
    ).filter(CostCenter.id == cc.id).first()
    return enrich_cost_center(cc)


@router.put("/{cc_id}", response_model=CostCenterResponse)
def update_cost_center(
    cc_id: UUID,
    data: CostCenterCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    cc = db.query(CostCenter).filter(CostCenter.id == cc_id).first()
    if not cc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")
    if data.code != cc.code:
        existing = db.query(CostCenter).filter(CostCenter.code == data.code, CostCenter.id != cc_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cost center code already exists")
    cc.code = data.code
    cc.name = data.name
    cc.department_id = data.department_id
    cc.responsible_user_id = data.responsible_user_id
    cc.budget_limit = data.budget_limit
    db.commit()
    cc = db.query(CostCenter).options(
        joinedload(CostCenter.department),
        joinedload(CostCenter.responsible_user),
    ).filter(CostCenter.id == cc_id).first()
    return enrich_cost_center(cc)


@router.delete("/{cc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cost_center(
    cc_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    cc = db.query(CostCenter).filter(CostCenter.id == cc_id).first()
    if not cc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")
    db.delete(cc)
    db.commit()
