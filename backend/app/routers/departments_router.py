from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Department
from app.schemas.schemas import DepartmentCreate, DepartmentResponse
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/departments", tags=["Departments"])


def build_tree(departments: List[Department], parent_id: Optional[UUID] = None) -> List[dict]:
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            node = {
                "id": dept.id,
                "name": dept.name,
                "company_id": dept.company_id,
                "parent_id": dept.parent_id,
                "created_at": dept.created_at,
                "children": build_tree(departments, dept.id),
            }
            tree.append(node)
    return tree


@router.get("/", response_model=List[DepartmentResponse])
def list_departments(
    company_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Department)
    if company_id:
        query = query.filter(Department.company_id == company_id)
    departments = query.offset(skip).limit(limit).all()
    return departments


@router.get("/tree", response_model=List[DepartmentResponse])
def get_department_tree(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    departments = db.query(Department).filter(Department.company_id == company_id).all()
    tree = build_tree(departments)
    return tree


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    if data.parent_id:
        parent = db.query(Department).filter(Department.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
    dept = Department(name=data.name, company_id=data.company_id, parent_id=data.parent_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: UUID,
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if data.parent_id:
        if data.parent_id == department_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department cannot be its own parent")
        parent = db.query(Department).filter(Department.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
    dept.name = data.name
    dept.company_id = data.company_id
    dept.parent_id = data.parent_id
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    children = db.query(Department).filter(Department.parent_id == department_id).count()
    if children > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with child departments",
        )
    db.delete(dept)
    db.commit()
