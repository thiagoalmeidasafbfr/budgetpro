from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.database import get_db
from app.auth.auth import get_current_user
from app.models.models import Lancamento, CentroDeCusto, ContaContabil
from app.schemas.lancamentos_schemas import (
    LancamentoResponse, LancamentoListResponse,
    BudgetPlanilhaRow, BudgetPlanilhaResponse,
)

router = APIRouter(prefix="/api/lancamentos", tags=["Lancamentos"])

FONTE_BUDGET = "Budget"
FONTE_RAZAO = "Razão"


@router.get("/", response_model=LancamentoListResponse)
def list_lancamentos(
    year: int = Query(2026),
    month: Optional[int] = Query(None, ge=1, le=12),
    fonte: Optional[str] = Query(None),
    centro_de_custo_id: Optional[UUID] = None,
    conta_contabil_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Lancamento).filter(extract("year", Lancamento.data_lancamento) == year)
    if month:
        q = q.filter(extract("month", Lancamento.data_lancamento) == month)
    if fonte:
        q = q.filter(Lancamento.fonte == fonte)
    if centro_de_custo_id:
        q = q.filter(Lancamento.centro_de_custo_id == str(centro_de_custo_id))
    if conta_contabil_id:
        q = q.filter(Lancamento.conta_contabil_id == str(conta_contabil_id))

    total = q.count()
    items = q.order_by(Lancamento.data_lancamento.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for l in items:
        cc = db.query(CentroDeCusto).filter(CentroDeCusto.id == l.centro_de_custo_id).first()
        conta = db.query(ContaContabil).filter(ContaContabil.id == l.conta_contabil_id).first()
        result.append(LancamentoResponse(
            id=l.id,
            data_lancamento=l.data_lancamento,
            conta_contabil_numero=conta.numero if conta else "",
            conta_contabil_nome=conta.nome if conta else "",
            centro_de_custo_codigo=cc.codigo if cc else "",
            centro_de_custo_nome=cc.nome if cc else "",
            fonte=l.fonte,
            valor=l.valor,
            observacao=l.observacao,
            nome_conta_contrapartida=l.nome_conta_contrapartida,
        ))

    return LancamentoListResponse(
        items=result, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/planilha", response_model=BudgetPlanilhaResponse)
def get_budget_planilha(
    year: int = Query(2026),
    centro_de_custo_id: Optional[UUID] = None,
    departamento_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    def build_query(fonte: str):
        q = db.query(
            Lancamento.centro_de_custo_id,
            Lancamento.conta_contabil_id,
            extract("month", Lancamento.data_lancamento).label("month"),
            func.sum(Lancamento.valor).label("total"),
        ).filter(
            extract("year", Lancamento.data_lancamento) == year,
            Lancamento.fonte == fonte,
        )
        if centro_de_custo_id:
            q = q.filter(Lancamento.centro_de_custo_id == str(centro_de_custo_id))
        if departamento_id:
            q = q.join(CentroDeCusto, Lancamento.centro_de_custo_id == CentroDeCusto.id).filter(
                CentroDeCusto.departamento_id == str(departamento_id)
            )
        return q.group_by(
            Lancamento.centro_de_custo_id, Lancamento.conta_contabil_id,
            extract("month", Lancamento.data_lancamento),
        ).all()

    def aggregate(rows):
        agg = {}
        for r in rows:
            key = (str(r.centro_de_custo_id), str(r.conta_contabil_id))
            if key not in agg:
                agg[key] = {}
            agg[key][int(r.month)] = Decimal(str(r.total))
        return agg

    budget_agg = aggregate(build_query(FONTE_BUDGET))
    razao_agg = aggregate(build_query(FONTE_RAZAO))
    all_keys = set(budget_agg.keys()) | set(razao_agg.keys())

    cc_cache, conta_cache = {}, {}

    def get_cc(cc_id):
        if cc_id not in cc_cache:
            cc_cache[cc_id] = db.query(CentroDeCusto).filter(CentroDeCusto.id == cc_id).first()
        return cc_cache[cc_id]

    def get_conta(conta_id):
        if conta_id not in conta_cache:
            conta_cache[conta_id] = db.query(ContaContabil).filter(ContaContabil.id == conta_id).first()
        return conta_cache[conta_id]

    ZERO = Decimal("0")
    rows_out = []
    for cc_id, conta_id in sorted(all_keys):
        cc = get_cc(cc_id)
        conta = get_conta(conta_id)
        if not cc or not conta:
            continue
        b = budget_agg.get((cc_id, conta_id), {})
        r = razao_agg.get((cc_id, conta_id), {})
        rows_out.append(BudgetPlanilhaRow(
            centro_de_custo_codigo=cc.codigo, centro_de_custo_nome=cc.nome,
            conta_contabil_numero=conta.numero, conta_contabil_nome=conta.nome,
            conta_agrupamento=getattr(conta, 'agrupamento_arvore', None),
            conta_dre=getattr(conta, 'dre', None),
            budget_jan=b.get(1, ZERO), budget_fev=b.get(2, ZERO), budget_mar=b.get(3, ZERO),
            budget_abr=b.get(4, ZERO), budget_mai=b.get(5, ZERO), budget_jun=b.get(6, ZERO),
            budget_jul=b.get(7, ZERO), budget_ago=b.get(8, ZERO), budget_set=b.get(9, ZERO),
            budget_out=b.get(10, ZERO), budget_nov=b.get(11, ZERO), budget_dez=b.get(12, ZERO),
            budget_total=sum(b.values(), ZERO),
            razao_jan=r.get(1, ZERO), razao_fev=r.get(2, ZERO), razao_mar=r.get(3, ZERO),
            razao_abr=r.get(4, ZERO), razao_mai=r.get(5, ZERO), razao_jun=r.get(6, ZERO),
            razao_jul=r.get(7, ZERO), razao_ago=r.get(8, ZERO), razao_set=r.get(9, ZERO),
            razao_out=r.get(10, ZERO), razao_nov=r.get(11, ZERO), razao_dez=r.get(12, ZERO),
            razao_total=sum(r.values(), ZERO),
        ))

    return BudgetPlanilhaResponse(rows=rows_out, total_rows=len(rows_out))


@router.get("/centros-de-custo")
def list_centros_de_custo(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = db.query(CentroDeCusto).order_by(CentroDeCusto.codigo).all()
    return [{"id": str(i.id), "codigo": i.codigo, "nome": i.nome} for i in items]


@router.get("/contas-contabeis")
def list_contas_contabeis(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = db.query(ContaContabil).order_by(ContaContabil.numero).all()
    return [{"id": str(i.id), "numero": i.numero, "nome": i.nome, "dre": getattr(i, 'dre', None)} for i in items]
