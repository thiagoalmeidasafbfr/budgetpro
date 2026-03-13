from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ---- Enums for schemas ----

class UserRoleEnum(str, Enum):
    admin = "admin"
    financial = "financial"
    manager = "manager"
    viewer = "viewer"


class AccountCategoryEnum(str, Enum):
    revenue = "revenue"
    cost = "cost"
    expense = "expense"
    investment = "investment"


class VersionStatusEnum(str, Enum):
    draft = "draft"
    under_review = "under_review"
    approved = "approved"
    locked = "locked"


class ActualSourceEnum(str, Enum):
    erp = "erp"
    manual = "manual"
    excel = "excel"
    api = "api"


class ForecastMethodEnum(str, Enum):
    linear = "linear"
    historical = "historical"
    manual = "manual"


class AuditActionEnum(str, Enum):
    create = "create"
    update = "update"
    delete = "delete"
    approve = "approve"
    lock = "lock"


class ApprovalStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ---- Auth ----

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ---- User ----

class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: UserRoleEnum = UserRoleEnum.viewer
    company_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: UserRoleEnum
    company_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---- Company ----

class CompanyCreate(BaseModel):
    name: str
    cnpj: Optional[str] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    cnpj: Optional[str] = None
    created_at: datetime


# ---- Department ----

class DepartmentCreate(BaseModel):
    name: str
    company_id: UUID
    parent_id: Optional[UUID] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    company_id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime
    children: List["DepartmentResponse"] = []


# ---- Cost Center ----

class CostCenterCreate(BaseModel):
    code: str
    name: str
    department_id: UUID
    responsible_user_id: Optional[UUID] = None
    budget_limit: Optional[Decimal] = None


class CostCenterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    department_id: UUID
    responsible_user_id: Optional[UUID] = None
    budget_limit: Optional[Decimal] = None
    created_at: datetime
    department_name: Optional[str] = None
    responsible_name: Optional[str] = None


# ---- Account ----

class AccountCreate(BaseModel):
    code: str
    name: str
    category: AccountCategoryEnum
    parent_id: Optional[UUID] = None
    is_active: bool = True


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: AccountCategoryEnum
    parent_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    children: List["AccountResponse"] = []


# ---- Budget Version ----

class BudgetVersionCreate(BaseModel):
    name: str
    year: int
    company_id: UUID
    description: Optional[str] = None


class BudgetVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[VersionStatusEnum] = None


class BudgetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    year: int
    status: VersionStatusEnum
    company_id: UUID
    created_by: UUID
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---- Budget ----

class BudgetCreate(BaseModel):
    version_id: UUID
    cost_center_id: UUID
    account_id: UUID
    jan: Decimal = Decimal("0")
    feb: Decimal = Decimal("0")
    mar: Decimal = Decimal("0")
    apr: Decimal = Decimal("0")
    may: Decimal = Decimal("0")
    jun: Decimal = Decimal("0")
    jul: Decimal = Decimal("0")
    aug: Decimal = Decimal("0")
    sep: Decimal = Decimal("0")
    oct: Decimal = Decimal("0")
    nov: Decimal = Decimal("0")
    dec: Decimal = Decimal("0")
    notes: Optional[str] = None


class BudgetUpdate(BaseModel):
    jan: Optional[Decimal] = None
    feb: Optional[Decimal] = None
    mar: Optional[Decimal] = None
    apr: Optional[Decimal] = None
    may: Optional[Decimal] = None
    jun: Optional[Decimal] = None
    jul: Optional[Decimal] = None
    aug: Optional[Decimal] = None
    sep: Optional[Decimal] = None
    oct: Optional[Decimal] = None
    nov: Optional[Decimal] = None
    dec: Optional[Decimal] = None
    notes: Optional[str] = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    cost_center_id: UUID
    account_id: UUID
    jan: Decimal
    feb: Decimal
    mar: Decimal
    apr: Decimal
    may: Decimal
    jun: Decimal
    jul: Decimal
    aug: Decimal
    sep: Decimal
    oct: Decimal
    nov: Decimal
    dec: Decimal
    total: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BudgetSpreadsheetRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    budget_id: UUID
    cost_center_code: str
    cost_center_name: str
    account_code: str
    account_name: str
    account_category: str
    jan: Decimal
    feb: Decimal
    mar: Decimal
    apr: Decimal
    may: Decimal
    jun: Decimal
    jul: Decimal
    aug: Decimal
    sep: Decimal
    oct: Decimal
    nov: Decimal
    dec: Decimal
    total: Decimal
    notes: Optional[str] = None


# ---- Actual ----

class ActualCreate(BaseModel):
    date: date
    account_id: UUID
    cost_center_id: UUID
    vendor: Optional[str] = None
    amount: Decimal
    description: Optional[str] = None
    source: ActualSourceEnum = ActualSourceEnum.manual


class ActualResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date
    account_id: UUID
    cost_center_id: UUID
    vendor: Optional[str] = None
    amount: Decimal
    description: Optional[str] = None
    source: ActualSourceEnum
    created_at: datetime


class ActualImport(BaseModel):
    items: List[ActualCreate]


# ---- Forecast ----

class ForecastCreate(BaseModel):
    version_id: UUID
    cost_center_id: UUID
    account_id: UUID
    jan: Decimal = Decimal("0")
    feb: Decimal = Decimal("0")
    mar: Decimal = Decimal("0")
    apr: Decimal = Decimal("0")
    may: Decimal = Decimal("0")
    jun: Decimal = Decimal("0")
    jul: Decimal = Decimal("0")
    aug: Decimal = Decimal("0")
    sep: Decimal = Decimal("0")
    oct: Decimal = Decimal("0")
    nov: Decimal = Decimal("0")
    dec: Decimal = Decimal("0")
    method: ForecastMethodEnum = ForecastMethodEnum.manual


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    cost_center_id: UUID
    account_id: UUID
    jan: Decimal
    feb: Decimal
    mar: Decimal
    apr: Decimal
    may: Decimal
    jun: Decimal
    jul: Decimal
    aug: Decimal
    sep: Decimal
    oct: Decimal
    nov: Decimal
    dec: Decimal
    total: Decimal
    method: ForecastMethodEnum
    generated_at: datetime
    created_by: UUID


class ForecastGenerate(BaseModel):
    version_id: UUID
    year: int
    method: ForecastMethodEnum = ForecastMethodEnum.linear
    cost_center_id: Optional[UUID] = None
    account_id: Optional[UUID] = None


# ---- Comment ----

class CommentCreate(BaseModel):
    budget_id: UUID
    text: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    budget_id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    user_name: Optional[str] = None


# ---- Dashboard ----

class DashboardKPIs(BaseModel):
    total_budget: Decimal
    total_actual: Decimal
    total_forecast: Decimal
    variance: Decimal
    variance_pct: Optional[float] = None
    budget_utilization_pct: Optional[float] = None


class MonthlyData(BaseModel):
    month: str
    budget: Decimal
    actual: Decimal
    forecast: Optional[Decimal] = None


class DashboardChartData(BaseModel):
    labels: List[str]
    datasets: List[dict]


class TopItem(BaseModel):
    name: str
    code: Optional[str] = None
    amount: Decimal
    percentage: Optional[float] = None


class CumulativeData(BaseModel):
    month: str
    cumulative_actual: Decimal
    cumulative_budget: Decimal


class BurnRateData(BaseModel):
    month: str
    monthly_spend: Decimal
    avg_monthly_spend: Decimal
    remaining_budget: Decimal


# ---- Audit ----

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    action: AuditActionEnum
    changes: Optional[dict] = None
    timestamp: datetime
    user_name: Optional[str] = None


# ---- Approval ----

class ApprovalWorkflowCreate(BaseModel):
    version_id: UUID
    comments: Optional[str] = None


class ApprovalWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    status: ApprovalStatusEnum
    requested_by: UUID
    approver_id: Optional[UUID] = None
    requested_at: datetime
    resolved_at: Optional[datetime] = None
    comments: Optional[str] = None


# ---- Pagination ----

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
