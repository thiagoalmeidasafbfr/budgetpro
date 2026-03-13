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


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"


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


# ===========================================================================
# MODELOS ORIGINAIS (compatibilidade com routers existentes)
# ===========================================================================

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    departments = relationship("Department", back_populates="company")
    users = relationship("User", back_populates="company")


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
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department_id = Column(UUIDType, ForeignKey("departments.id"), nullable=False)
    responsible_user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    budget_limit = Column(Numeric(18, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    department = relationship("Department", back_populates="cost_centers")
    responsible = relationship("User", foreign_keys=[responsible_user_id])
    budgets = relationship("Budget", back_populates="cost_center")
    actuals = relationship("Actual", back_populates="cost_center")
    forecasts = relationship("Forecast", back_populates="cost_center")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    code = Column(String(30), unique=True, nullable=False, index=True)
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

    budgets = relationship("Budget", back_populates="version")
    forecasts = relationship("Forecast", back_populates="version")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    version_id = Column(UUIDType, ForeignKey("budget_versions.id"), nullable=False)
    cost_center_id = Column(UUIDType, ForeignKey("cost_centers.id"), nullable=False)
    account_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=False)
    jan = Column(Numeric(18, 2), default=0, nullable=False)
    feb = Column(Numeric(18, 2), default=0, nullable=False)
    mar = Column(Numeric(18, 2), default=0, nullable=False)
    apr = Column(Numeric(18, 2), default=0, nullable=False)
    may = Column(Numeric(18, 2), default=0, nullable=False)
    jun = Column(Numeric(18, 2), default=0, nullable=False)
    jul = Column(Numeric(18, 2), default=0, nullable=False)
    aug = Column(Numeric(18, 2), default=0, nullable=False)
    sep = Column(Numeric(18, 2), default=0, nullable=False)
    oct = Column(Numeric(18, 2), default=0, nullable=False)
    nov = Column(Numeric(18, 2), default=0, nullable=False)
    dec = Column(Numeric(18, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    version = relationship("BudgetVersion", back_populates="budgets")
    cost_center = relationship("CostCenter", back_populates="budgets")
    account = relationship("Account", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("version_id", "cost_center_id", "account_id", name="uq_budget_version_cc_account"),
    )

    @property
    def total(self):
        return sum([
            self.jan or 0, self.feb or 0, self.mar or 0, self.apr or 0,
            self.may or 0, self.jun or 0, self.jul or 0, self.aug or 0,
            self.sep or 0, self.oct or 0, self.nov or 0, self.dec or 0,
        ])


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


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    version_id = Column(UUIDType, ForeignKey("budget_versions.id"), nullable=False)
    cost_center_id = Column(UUIDType, ForeignKey("cost_centers.id"), nullable=False)
    account_id = Column(UUIDType, ForeignKey("accounts.id"), nullable=False)
    jan = Column(Numeric(18, 2), default=0, nullable=False)
    feb = Column(Numeric(18, 2), default=0, nullable=False)
    mar = Column(Numeric(18, 2), default=0, nullable=False)
    apr = Column(Numeric(18, 2), default=0, nullable=False)
    may = Column(Numeric(18, 2), default=0, nullable=False)
    jun = Column(Numeric(18, 2), default=0, nullable=False)
    jul = Column(Numeric(18, 2), default=0, nullable=False)
    aug = Column(Numeric(18, 2), default=0, nullable=False)
    sep = Column(Numeric(18, 2), default=0, nullable=False)
    oct = Column(Numeric(18, 2), default=0, nullable=False)
    nov = Column(Numeric(18, 2), default=0, nullable=False)
    dec = Column(Numeric(18, 2), default=0, nullable=False)
    method = Column(Enum(ForecastMethod), nullable=False, default=ForecastMethod.manual)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    version = relationship("BudgetVersion", back_populates="forecasts")
    cost_center = relationship("CostCenter", back_populates="forecasts")
    account = relationship("Account", back_populates="forecasts")

    @property
    def total(self):
        return sum([
            self.jan or 0, self.feb or 0, self.mar or 0, self.apr or 0,
            self.may or 0, self.jun or 0, self.jul or 0, self.aug or 0,
            self.sep or 0, self.oct or 0, self.nov or 0, self.dec or 0,
        ])


# ===========================================================================
# MODELOS NOVOS — Hierarquia real do cliente
# ===========================================================================

class Area(Base):
    """Nível 1 da hierarquia de centros de custo (ex: B.2 - Backoffice)"""
    __tablename__ = "areas"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    departamentos = relationship("Departamento", back_populates="area")


class Departamento(Base):
    """Nível 2 da hierarquia de centros de custo (ex: B.202 - Finanças)"""
    __tablename__ = "departamentos"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    area_id = Column(UUIDType, ForeignKey("areas.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    area = relationship("Area", back_populates="departamentos")
    centros_de_custo = relationship("CentroDeCusto", back_populates="departamento")


class CentroDeCusto(Base):
    """Nível 3 (analítico) da hierarquia de centros de custo (ex: B.202001 - Tesouraria)"""
    __tablename__ = "centros_de_custo"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    departamento_id = Column(UUIDType, ForeignKey("departamentos.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    departamento = relationship("Departamento", back_populates="centros_de_custo")
    lancamentos = relationship("Lancamento", back_populates="centro_de_custo")


class ContaContabil(Base):
    """Plano de contas com hierarquia de 5 níveis (ex: 3.1.01.001.001 - TV ABERTA)"""
    __tablename__ = "contas_contabeis"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    numero = Column(String(30), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    agrupamento_arvore = Column(String(255), nullable=True)
    dre = Column(String(100), nullable=True)
    nivel1 = Column(String(10), nullable=True)
    nivel2 = Column(String(10), nullable=True)
    nivel3 = Column(String(15), nullable=True)
    nivel4 = Column(String(20), nullable=True)
    nivel5 = Column(String(30), nullable=True)
    is_analitica = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lancamentos = relationship("Lancamento", back_populates="conta_contabil")


class Lancamento(Base):
    """
    Tabela fato unificada para Budget e Realizado/Razão.
    A coluna 'fonte' diferencia os registros: 'Budget' ou 'Razão'.
    """
    __tablename__ = "lancamentos"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    data_lancamento = Column(Date, nullable=False, index=True)
    conta_contabil_id = Column(UUIDType, ForeignKey("contas_contabeis.id"), nullable=False)
    centro_de_custo_id = Column(UUIDType, ForeignKey("centros_de_custo.id"), nullable=False)
    nome_conta_contrapartida = Column(String(255), nullable=True)
    fonte = Column(String(20), nullable=False, index=True)
    observacao = Column(Text, nullable=True)
    valor = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conta_contabil = relationship("ContaContabil", back_populates="lancamentos")
    centro_de_custo = relationship("CentroDeCusto", back_populates="lancamentos")

    __table_args__ = (
        Index("ix_lancamentos_data_fonte", "data_lancamento", "fonte"),
        Index("ix_lancamentos_conta", "conta_contabil_id"),
        Index("ix_lancamentos_cc", "centro_de_custo_id"),
    )


# ===========================================================================
# USUÁRIOS E AUDITORIA
# ===========================================================================

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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False)
    action = Column(Enum(AuditAction), nullable=False)
    changes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
