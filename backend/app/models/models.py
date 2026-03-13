import uuid
import enum
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column, String, Boolean, Integer, Numeric, Date, Text, JSON,
    ForeignKey, DateTime, Enum, UniqueConstraint, Index, event, TypeDecorator
)
from sqlalchemy.orm import relationship
from app.database import Base


class UUIDType(TypeDecorator):
    """Platform-independent UUID type. Uses String(36) for SQLite compatibility."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
        return value


def gen_uuid():
    return str(uuid.uuid4())


# ---- Enums ----

class UserRole(str, enum.Enum):
    admin = "admin"
    financial = "financial"
    manager = "manager"
    viewer = "viewer"


class AccountCategory(str, enum.Enum):
    revenue = "revenue"
    cost = "cost"
    expense = "expense"
    investment = "investment"


class VersionStatus(str, enum.Enum):
    draft = "draft"
    under_review = "under_review"
    approved = "approved"
    locked = "locked"


class ActualSource(str, enum.Enum):
    erp = "erp"
    manual = "manual"
    excel = "excel"
    api = "api"


class ForecastMethod(str, enum.Enum):
    linear = "linear"
    historical = "historical"
    manual = "manual"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    approve = "approve"
    lock = "lock"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ---- Models ----

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="company")
    departments = relationship("Department", back_populates="company")
    budget_versions = relationship("BudgetVersion", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    company_id = Column(UUIDType, ForeignKey("companies.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="users")
    cost_centers = relationship("CostCenter", back_populates="responsible_user")
    created_versions = relationship("BudgetVersion", back_populates="created_by_user", foreign_keys="BudgetVersion.created_by")
    comments = relationship("Comment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    forecasts = relationship("Forecast", back_populates="created_by_user")
    requested_approvals = relationship("ApprovalWorkflow", back_populates="requester", foreign_keys="ApprovalWorkflow.requested_by")
    approved_workflows = relationship("ApprovalWorkflow", back_populates="approver", foreign_keys="ApprovalWorkflow.approver_id")


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    company_id = Column(UUIDType, ForeignKey("companies.id"), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="departments")
    parent = relationship("Department", remote_side="Department.id", back_populates="children")
    children = relationship("Department", back_populates="parent")
    cost_centers = relationship("CostCenter", back_populates="department")


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department_id = Column(UUIDType, ForeignKey("departments.id"), nullable=False)
    responsible_user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    budget_limit = Column(Numeric(18, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    department = relationship("Department", back_populates="cost_centers")
    responsible_user = relationship("User", back_populates="cost_centers")
    budgets = relationship("Budget", back_populates="cost_center")
    actuals = relationship("Actual", back_populates="cost_center")
    forecasts = relationship("Forecast", back_populates="cost_center")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(Enum(AccountCategory), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    parent = relationship("Account", remote_side="Account.id", back_populates="children")
    children = relationship("Account", back_populates="parent")
    budgets = relationship("Budget", back_populates="account")
    actuals = relationship("Actual", back_populates="account")
    forecasts = relationship("Forecast", back_populates="account")


class BudgetVersion(Base):
    __tablename__ = "budget_versions"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(Enum(VersionStatus), nullable=False, default=VersionStatus.draft)
    company_id = Column(UUIDType, ForeignKey("companies.id"), nullable=False)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="budget_versions")
    created_by_user = relationship("User", back_populates="created_versions", foreign_keys=[created_by])
    budgets = relationship("Budget", back_populates="version", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="version", cascade="all, delete-orphan")
    approval_workflows = relationship("ApprovalWorkflow", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_budget_versions_year", "year"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    version_id = Column(UUIDType, ForeignKey("budget_versions.id"), nullable=False)
    cost_center_id = Column(UUIDType, ForeignKey("cost_centers.id"), nullable=False)
    account_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=False)
    jan = Column(Numeric(18, 2), default=0)
    feb = Column(Numeric(18, 2), default=0)
    mar = Column(Numeric(18, 2), default=0)
    apr = Column(Numeric(18, 2), default=0)
    may = Column(Numeric(18, 2), default=0)
    jun = Column(Numeric(18, 2), default=0)
    jul = Column(Numeric(18, 2), default=0)
    aug = Column(Numeric(18, 2), default=0)
    sep = Column(Numeric(18, 2), default=0)
    oct = Column(Numeric(18, 2), default=0)
    nov = Column(Numeric(18, 2), default=0)
    dec = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    version = relationship("BudgetVersion", back_populates="budgets")
    cost_center = relationship("CostCenter", back_populates="budgets")
    account = relationship("Account", back_populates="budgets")
    comments = relationship("Comment", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "cost_center_id", "account_id", name="uq_budget_version_cc_account"),
        Index("ix_budgets_version_id", "version_id"),
    )


def compute_budget_total(mapper, connection, target):
    months = [target.jan, target.feb, target.mar, target.apr, target.may, target.jun,
              target.jul, target.aug, target.sep, target.oct, target.nov, target.dec]
    target.total = sum(m or Decimal("0") for m in months)


event.listen(Budget, "before_insert", compute_budget_total)
event.listen(Budget, "before_update", compute_budget_total)


class Actual(Base):
    __tablename__ = "actuals"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    date = Column(Date, nullable=False, index=True)
    account_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=False)
    cost_center_id = Column(UUIDType, ForeignKey("cost_centers.id"), nullable=False)
    vendor = Column(String(255), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(Enum(ActualSource), nullable=False, default=ActualSource.manual)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    account = relationship("Account", back_populates="actuals")
    cost_center = relationship("CostCenter", back_populates="actuals")

    __table_args__ = (
        Index("ix_actuals_date_account", "date", "account_id"),
        Index("ix_actuals_cost_center", "cost_center_id"),
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    version_id = Column(UUIDType, ForeignKey("budget_versions.id"), nullable=False)
    cost_center_id = Column(UUIDType, ForeignKey("cost_centers.id"), nullable=False)
    account_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=False)
    jan = Column(Numeric(18, 2), default=0)
    feb = Column(Numeric(18, 2), default=0)
    mar = Column(Numeric(18, 2), default=0)
    apr = Column(Numeric(18, 2), default=0)
    may = Column(Numeric(18, 2), default=0)
    jun = Column(Numeric(18, 2), default=0)
    jul = Column(Numeric(18, 2), default=0)
    aug = Column(Numeric(18, 2), default=0)
    sep = Column(Numeric(18, 2), default=0)
    oct = Column(Numeric(18, 2), default=0)
    nov = Column(Numeric(18, 2), default=0)
    dec = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), default=0)
    method = Column(Enum(ForecastMethod), nullable=False, default=ForecastMethod.linear)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=False)

    version = relationship("BudgetVersion", back_populates="forecasts")
    cost_center = relationship("CostCenter", back_populates="forecasts")
    account = relationship("Account", back_populates="forecasts")
    created_by_user = relationship("User", back_populates="forecasts")

    __table_args__ = (
        Index("ix_forecasts_version_id", "version_id"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    budget_id = Column(UUIDType, ForeignKey("budgets.id"), nullable=False)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    budget = relationship("Budget", back_populates="comments")
    user = relationship("User", back_populates="comments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUIDType, nullable=False)
    action = Column(Enum(AuditAction), nullable=False)
    changes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    version_id = Column(UUIDType, ForeignKey("budget_versions.id"), nullable=False)
    status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending)
    requested_by = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    approver_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)

    version = relationship("BudgetVersion", back_populates="approval_workflows")
    requester = relationship("User", back_populates="requested_approvals", foreign_keys=[requested_by])
    approver = relationship("User", back_populates="approved_workflows", foreign_keys=[approver_id])
