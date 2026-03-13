from uuid import UUID
from decimal import Decimal
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.models import Budget, BudgetVersion, CostCenter, Account, VersionStatus, AuditLog, AuditAction, AccountCategory
from app.schemas.schemas import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSpreadsheetRow
from app.auth.auth import get_current_user, require_role
from app.services.excel_service import import_budget_excel, export_budget_excel

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def check_version_editable(version: BudgetVersion):
    if version.status == VersionStatus.locked:
        raise HTTPException(status_code=400, detail="Cannot modify budgets in a locked version")


@router.get("/", response_model=List[BudgetResponse])
def list_budgets(
    version_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Budget)
    if version_id:
        query = query.filter(Budget.version_id == version_id)
    if cost_center_id:
        query = query.filter(Budget.cost_center_id == cost_center_id)
    if account_id:
        query = query.filter(Budget.account_id == account_id)
    if category:
        try:
            cat = AccountCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        query = query.join(Account).filter(Account.category == cat)
    return query.offset(skip).limit(limit).all()


@router.get("/spreadsheet/{version_id}", response_model=List[BudgetSpreadsheetRow])
def get_spreadsheet(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")

    budgets = (
        db.query(Budget)
        .options(joinedload(Budget.cost_center), joinedload(Budget.account))
        .filter(Budget.version_id == version_id)
        .all()
    )

    rows = []
    for b in budgets:
        rows.append(BudgetSpreadsheetRow(
            budget_id=b.id,
            cost_center_code=b.cost_center.code,
            cost_center_name=b.cost_center.name,
            account_code=b.account.code,
            account_name=b.account.name,
            account_category=b.account.category.value,
            jan=b.jan or 0, feb=b.feb or 0, mar=b.mar or 0,
            apr=b.apr or 0, may=b.may or 0, jun=b.jun or 0,
            jul=b.jul or 0, aug=b.aug or 0, sep=b.sep or 0,
            oct=b.oct or 0, nov=b.nov or 0, dec=b.dec or 0,
            total=b.total or 0,
            notes=b.notes,
        ))

    rows.sort(key=lambda r: (r.cost_center_code, r.account_code))
    return rows


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == data.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")
    check_version_editable(version)

    existing = db.query(Budget).filter(
        Budget.version_id == data.version_id,
        Budget.cost_center_id == data.cost_center_id,
        Budget.account_id == data.account_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Budget row already exists for this version/cost-center/account combination")

    budget = Budget(
        version_id=data.version_id,
        cost_center_id=data.cost_center_id,
        account_id=data.account_id,
        jan=data.jan, feb=data.feb, mar=data.mar,
        apr=data.apr, may=data.may, jun=data.jun,
        jul=data.jul, aug=data.aug, sep=data.sep,
        oct=data.oct, nov=data.nov, dec=data.dec,
        notes=data.notes,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial", "manager"])),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    version = db.query(BudgetVersion).filter(BudgetVersion.id == budget.version_id).first()
    check_version_editable(version)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    db.commit()
    db.refresh(budget)

    audit = AuditLog(
        user_id=current_user.id,
        entity_type="Budget",
        entity_id=budget.id,
        action=AuditAction.update,
        changes=update_data,
    )
    db.add(audit)
    db.commit()

    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    version = db.query(BudgetVersion).filter(BudgetVersion.id == budget.version_id).first()
    check_version_editable(version)
    db.delete(budget)
    db.commit()


@router.post("/import-excel/{version_id}")
def import_excel(
    version_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")
    check_version_editable(version)

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx)")

    content = file.file.read()
    result = import_budget_excel(db, version_id, content, current_user.id)
    return result


@router.post("/export-excel/{version_id}")
def export_excel(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Budget version not found")

    output = export_budget_excel(db, version_id, version.name)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=budget_{version.name}_{version.year}.xlsx"},
    )
