from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Account, AccountCategory
from app.schemas.schemas import AccountCreate, AccountResponse
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


def build_account_tree(accounts: List[Account], parent_id: Optional[UUID] = None) -> List[dict]:
    tree = []
    for acc in accounts:
        if acc.parent_id == parent_id:
            node = {
                "id": acc.id,
                "code": acc.code,
                "name": acc.name,
                "category": acc.category.value,
                "parent_id": acc.parent_id,
                "is_active": acc.is_active,
                "created_at": acc.created_at,
                "children": build_account_tree(accounts, acc.id),
            }
            tree.append(node)
    return tree


@router.get("/", response_model=List[AccountResponse])
def list_accounts(
    category: Optional[str] = None,
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Account)
    if category:
        try:
            cat_enum = AccountCategory(category)
            query = query.filter(Account.category == cat_enum)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid category: {category}")
    if active_only:
        query = query.filter(Account.is_active == True)
    return query.order_by(Account.code).offset(skip).limit(limit).all()


@router.get("/tree", response_model=List[AccountResponse])
def get_account_tree(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Account)
    if category:
        try:
            cat_enum = AccountCategory(category)
            query = query.filter(Account.category == cat_enum)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid category: {category}")
    accounts = query.order_by(Account.code).all()
    return build_account_tree(accounts)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    existing = db.query(Account).filter(Account.code == data.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")
    if data.parent_id:
        parent = db.query(Account).filter(Account.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent account not found")
    account = Account(
        code=data.code,
        name=data.name,
        category=data.category,
        parent_id=data.parent_id,
        is_active=data.is_active,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if data.code != account.code:
        existing = db.query(Account).filter(Account.code == data.code, Account.id != account_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")
    account.code = data.code
    account.name = data.name
    account.category = data.category
    account.parent_id = data.parent_id
    account.is_active = data.is_active
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    children = db.query(Account).filter(Account.parent_id == account_id).count()
    if children > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete account with children")
    db.delete(account)
    db.commit()
