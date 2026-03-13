from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal


class LancamentoResponse(BaseModel):
    id: UUID
    data_lancamento: date
    conta_contabil_numero: str
    conta_contabil_nome: str
    centro_de_custo_codigo: str
    centro_de_custo_nome: str
    fonte: str
    valor: Decimal
    observacao: Optional[str] = None
    nome_conta_contrapartida: Optional[str] = None

    class Config:
        from_attributes = True


class LancamentoListResponse(BaseModel):
    items: List[LancamentoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BudgetPlanilhaRow(BaseModel):
    centro_de_custo_codigo: str
    centro_de_custo_nome: str
    conta_contabil_numero: str
    conta_contabil_nome: str
    conta_agrupamento: Optional[str] = None
    conta_dre: Optional[str] = None
    budget_jan: Decimal
    budget_fev: Decimal
    budget_mar: Decimal
    budget_abr: Decimal
    budget_mai: Decimal
    budget_jun: Decimal
    budget_jul: Decimal
    budget_ago: Decimal
    budget_set: Decimal
    budget_out: Decimal
    budget_nov: Decimal
    budget_dez: Decimal
    budget_total: Decimal
    razao_jan: Decimal
    razao_fev: Decimal
    razao_mar: Decimal
    razao_abr: Decimal
    razao_mai: Decimal
    razao_jun: Decimal
    razao_jul: Decimal
    razao_ago: Decimal
    razao_set: Decimal
    razao_out: Decimal
    razao_nov: Decimal
    razao_dez: Decimal
    razao_total: Decimal


class BudgetPlanilhaResponse(BaseModel):
    rows: List[BudgetPlanilhaRow]
    total_rows: int
