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


# ---- Dimensão: Hierarquia de Centros de Custo ----

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


# ---- Dimensão: Hierarquia do Plano de Contas ----

class ContaContabil(Base):
    """Plano de contas com hierarquia de 5 níveis (ex: 3.1.01.001.001 - TV ABERTA)"""
    __tablename__ = "contas_contabeis"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    numero = Column(String(30), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    agrupamento_arvore = Column(String(255), nullable=True)  # ex: Broadcast Revenue
    dre = Column(String(100), nullable=True)  # ex: Revenue
    # Hierarquia derivada do número da conta
    nivel1 = Column(String(10), nullable=True)  # ex: 3
    nivel2 = Column(String(10), nullable=True)  # ex: 3.1
    nivel3 = Column(String(15), nullable=True)  # ex: 3.1.01
    nivel4 = Column(String(20), nullable=True)  # ex: 3.1.01.001
    nivel5 = Column(String(30), nullable=True)  # ex: 3.1.01.001.001 (analítico)
    is_analitica = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lancamentos = relationship("Lancamento", back_populates="conta_contabil")


# ---- Tabela Fato: Lançamentos (Budget + Realizado) ----

class Lancamento(Base):
    """
    Tabela fato unificada para Budget e Realizado/Razão.
    A coluna 'fonte' diferencia os registros: 'Budget' ou 'Razão'.
    Estrutura baseada nas planilhas reais do cliente.
    """
    __tablename__ = "lancamentos"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    data_lancamento = Column(Date, nullable=False, index=True)
    conta_contabil_id = Column(UUIDType, ForeignKey("contas_contabeis.id"), nullable=False)
    centro_de_custo_id = Column(UUIDType, ForeignKey("centros_de_custo.id"), nullable=False)
    nome_conta_contrapartida = Column(String(255), nullable=True)
    fonte = Column(String(20), nullable=False, index=True)  # 'Budget' ou 'Razão'
    observacao = Column(Text, nullable=True)
    valor = Column(Numeric(18, 2), nullable=False)  # Débito/Crédito (MC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conta_contabil = relationship("ContaContabil", back_populates="lancamentos")
    centro_de_custo = relationship("CentroDeCusto", back_populates="lancamentos")

    __table_args__ = (
        Index("ix_lancamentos_data_fonte", "data_lancamento", "fonte"),
        Index("ix_lancamentos_conta", "conta_contabil_id"),
        Index("ix_lancamentos_cc", "centro_de_custo_id"),
    )


# ---- Usuários e Autenticação (mantidos) ----

class User(Base):
    __tablename__ = "users"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False)
    action = Column(Enum(AuditAction), nullable=False)
    changes = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
