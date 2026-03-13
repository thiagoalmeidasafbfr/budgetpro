from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.database import get_db
from app.models.models import BudgetVersion, Budget, VersionStatus, AuditLog, AuditAction, ApprovalWorkflow, ApprovalStatus
from app.schemas.schemas import BudgetVersionCreate, BudgetVersionUpdate, BudgetVersionResponse
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/budget-versions", tags=["Budget Versions"])

VALID_TRANSITIONS = {
    VersionStatus.draft: [VersionStatus.under_review],
    VersionStatus.under_review: [VersionStatus.approved, VersionStatus.draft],
    VersionStatus.approved: [VersionStatus.locked, VersionStatus.under_review],
    VersionStatus.locked: [],
}


@router.get("/", response_model=List[BudgetVersionResponse])
def list_versions(
    year: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    company_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(BudgetVersion)
    if year:
        query = query.filter(BudgetVersion.year == year)
    if status_filter:
        try:
            s = VersionStatus(status_filter)
            query = query.filter(BudgetVersion.status == s)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    if company_id:
        query = query.filter(BudgetVersion.company_id == company_id)
    return query.order_by(BudgetVersion.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{version_id}", response_model=BudgetVersionResponse)
def get_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")
    return version


@router.post("/", response_model=BudgetVersionResponse, status_code=status.HTTP_201_CREATED)
def create_version(
    data: BudgetVersionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    version = BudgetVersion(
        name=data.name,
        year=data.year,
        company_id=data.company_id,
        created_by=current_user.id,
        description=data.description,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    audit = AuditLog(
        user_id=current_user.id,
        entity_type="BudgetVersion",
        entity_id=version.id,
        action=AuditAction.create,
        changes={"name": data.name, "year": data.year},
    )
    db.add(audit)
    db.commit()
    return version


@router.put("/{version_id}", response_model=BudgetVersionResponse)
def update_version(
    version_id: UUID,
    data: BudgetVersionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")
    if version.status == VersionStatus.locked:
        raise HTTPException(status_code=400, detail="Locked versions cannot be edited")

    changes = {}
    if data.name is not None:
        changes["name"] = {"old": version.name, "new": data.name}
        version.name = data.name
    if data.description is not None:
        changes["description"] = {"old": version.description, "new": data.description}
        version.description = data.description
    if data.status is not None:
        new_status = VersionStatus(data.status.value)
        allowed = VALID_TRANSITIONS.get(version.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{version.status.value}' to '{new_status.value}'. Allowed: {[s.value for s in allowed]}",
            )
        changes["status"] = {"old": version.status.value, "new": new_status.value}
        version.status = new_status

        action = AuditAction.update
        if new_status == VersionStatus.approved:
            action = AuditAction.approve
        elif new_status == VersionStatus.locked:
            action = AuditAction.lock

        audit = AuditLog(
            user_id=current_user.id,
            entity_type="BudgetVersion",
            entity_id=version.id,
            action=action,
            changes=changes,
        )
        db.add(audit)

    db.commit()
    db.refresh(version)
    return version


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")
    if version.status == VersionStatus.locked:
        raise HTTPException(status_code=400, detail="Cannot delete locked version")
    db.delete(version)
    db.commit()


@router.get("/compare/{version_a_id}/{version_b_id}")
def compare_versions(
    version_a_id: UUID,
    version_b_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version_a = db.query(BudgetVersion).filter(BudgetVersion.id == version_a_id).first()
    version_b = db.query(BudgetVersion).filter(BudgetVersion.id == version_b_id).first()
    if not version_a or not version_b:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    budgets_a = db.query(Budget).filter(Budget.version_id == version_a_id).all()
    budgets_b = db.query(Budget).filter(Budget.version_id == version_b_id).all()

    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

    key_a = {(str(b.cost_center_id), str(b.account_id)): b for b in budgets_a}
    key_b = {(str(b.cost_center_id), str(b.account_id)): b for b in budgets_b}

    all_keys = set(key_a.keys()) | set(key_b.keys())
    comparison = []

    for key in sorted(all_keys):
        ba = key_a.get(key)
        bb = key_b.get(key)

        row = {
            "cost_center_id": key[0],
            "account_id": key[1],
            "version_a": {},
            "version_b": {},
            "diff": {},
        }

        total_a = Decimal("0")
        total_b = Decimal("0")
        for m in months:
            val_a = getattr(ba, m, Decimal("0")) or Decimal("0") if ba else Decimal("0")
            val_b = getattr(bb, m, Decimal("0")) or Decimal("0") if bb else Decimal("0")
            total_a += val_a
            total_b += val_b
            row["version_a"][m] = float(val_a)
            row["version_b"][m] = float(val_b)
            row["diff"][m] = float(val_b - val_a)

        row["version_a"]["total"] = float(total_a)
        row["version_b"]["total"] = float(total_b)
        row["diff"]["total"] = float(total_b - total_a)
        comparison.append(row)

    return {
        "version_a": {"id": str(version_a.id), "name": version_a.name, "status": version_a.status.value},
        "version_b": {"id": str(version_b.id), "name": version_b.name, "status": version_b.status.value},
        "rows": comparison,
    }
