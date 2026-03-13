from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Company
from app.schemas.schemas import CompanyCreate, CompanyResponse
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.get("/", response_model=List[CompanyResponse])
def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Company).offset(skip).limit(limit).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    if data.cnpj:
        existing = db.query(Company).filter(Company.cnpj == data.cnpj).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ already registered")
    company = Company(name=data.name, cnpj=data.cnpj)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.name = data.name
    if data.cnpj:
        existing = db.query(Company).filter(Company.cnpj == data.cnpj, Company.id != company_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ already registered")
        company.cnpj = data.cnpj
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    db.delete(company)
    db.commit()
