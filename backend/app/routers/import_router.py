import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Area, Departamento, CentroDeCusto, ContaContabil, Lancamento
from app.auth.auth import get_current_user, require_role

router = APIRouter(prefix="/api/import", tags=["Import"])


def parse_csv(content: bytes) -> list[dict]:
    """Detecta separador (vírgula ou ponto-e-vírgula) e retorna lista de dicts."""
    text = content.decode("utf-8-sig").strip()
    # Detecta separador
    first_line = text.split("\n")[0]
    sep = ";" if first_line.count(";") >= first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=sep)
    return [row for row in reader]


def normalize_key(k: str) -> str:
    return k.strip().lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")


# ---------------------------------------------------------------------------
# 1. Importar Dimensionamento de Centros de Custo
# ---------------------------------------------------------------------------
# Colunas esperadas (case-insensitive):
# Centro de Custo | Nome do Centro de Custo | Depart | Nome Departamento | Área | Nome Área

@router.post("/cost-centers", status_code=status.HTTP_200_OK)
def import_cost_centers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    content = file.file.read()
    rows = parse_csv(content)
    if not rows:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou sem dados.")

    # Normaliza cabeçalhos
    normalized = [{normalize_key(k): v.strip() for k, v in row.items()} for row in rows]

    created_areas = 0
    created_deps = 0
    created_ccs = 0
    errors = []

    for i, row in enumerate(normalized, start=2):
        try:
            # Campos área
            area_cod = row.get("área") or row.get("area") or ""
            area_nome = row.get("nome_área") or row.get("nome_area") or ""
            # Campos departamento
            dep_cod = row.get("depart") or row.get("departamento") or ""
            dep_nome = row.get("nome_departamento") or row.get("nome_depart") or ""
            # Campos centro de custo
            cc_cod = row.get("centro_de_custo") or ""
            cc_nome = row.get("nome_do_centro_de_custo") or row.get("nome_centro_de_custo") or ""

            if not cc_cod:
                errors.append(f"Linha {i}: código do centro de custo vazio.")
                continue

            # Upsert Área
            area = None
            if area_cod:
                area = db.query(Area).filter(Area.codigo == area_cod).first()
                if not area:
                    area = Area(codigo=area_cod, nome=area_nome or area_cod)
                    db.add(area)
                    db.flush()
                    created_areas += 1
                elif area_nome and area.nome != area_nome:
                    area.nome = area_nome

            # Upsert Departamento
            dep = None
            if dep_cod and area:
                dep = db.query(Departamento).filter(Departamento.codigo == dep_cod).first()
                if not dep:
                    dep = Departamento(codigo=dep_cod, nome=dep_nome or dep_cod, area_id=area.id)
                    db.add(dep)
                    db.flush()
                    created_deps += 1
                elif dep_nome and dep.nome != dep_nome:
                    dep.nome = dep_nome

            # Upsert Centro de Custo
            if dep is None:
                # Tenta buscar qualquer departamento existente como fallback
                dep = db.query(Departamento).first()
                if not dep:
                    # Cria área e dep genéricos se não existirem
                    gen_area = db.query(Area).filter(Area.codigo == "GEN").first()
                    if not gen_area:
                        gen_area = Area(codigo="GEN", nome="Geral")
                        db.add(gen_area)
                        db.flush()
                    dep = Departamento(codigo="GEN", nome="Geral", area_id=gen_area.id)
                    db.add(dep)
                    db.flush()

            cc = db.query(CentroDeCusto).filter(CentroDeCusto.codigo == cc_cod).first()
            if not cc:
                cc = CentroDeCusto(codigo=cc_cod, nome=cc_nome or cc_cod, departamento_id=dep.id)
                db.add(cc)
                created_ccs += 1
            else:
                if cc_nome:
                    cc.nome = cc_nome

        except Exception as e:
            errors.append(f"Linha {i}: {str(e)}")

    db.commit()

    return {
        "message": "Importação concluída.",
        "areas_criadas": created_areas,
        "departamentos_criados": created_deps,
        "centros_de_custo_criados": created_ccs,
        "erros": errors[:20],
    }


# ---------------------------------------------------------------------------
# 2. Importar Plano de Contas
# ---------------------------------------------------------------------------
# Colunas esperadas:
# Número Conta Contábil | Nome Conta Contábil | Agrupamento Arvore | DRE

@router.post("/accounts", status_code=status.HTTP_200_OK)
def import_accounts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    content = file.file.read()
    rows = parse_csv(content)
    if not rows:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou sem dados.")

    normalized = [{normalize_key(k): v.strip() for k, v in row.items()} for row in rows]

    created = 0
    updated = 0
    errors = []

    for i, row in enumerate(normalized, start=2):
        try:
            numero = (
                row.get("número_conta_contábil")
                or row.get("numero_conta_contabil")
                or row.get("número_conta")
                or row.get("numero")
                or ""
            ).strip()
            nome = (
                row.get("nome_conta_contábil")
                or row.get("nome_conta_contabil")
                or row.get("nome")
                or ""
            ).strip()
            agrupamento = (
                row.get("agrupamento_arvore")
                or row.get("agrupamento")
                or ""
            ).strip() or None
            dre = (row.get("dre") or "").strip() or None

            if not numero or not nome:
                errors.append(f"Linha {i}: número ou nome da conta vazio.")
                continue

            # Deriva níveis hierárquicos a partir do número
            partes = numero.split(".")
            nivel1 = partes[0] if len(partes) >= 1 else None
            nivel2 = ".".join(partes[:2]) if len(partes) >= 2 else None
            nivel3 = ".".join(partes[:3]) if len(partes) >= 3 else None
            nivel4 = ".".join(partes[:4]) if len(partes) >= 4 else None
            nivel5 = numero if len(partes) >= 5 else None
            is_analitica = len(partes) >= 5

            conta = db.query(ContaContabil).filter(ContaContabil.numero == numero).first()
            if not conta:
                conta = ContaContabil(
                    numero=numero,
                    nome=nome,
                    agrupamento_arvore=agrupamento,
                    dre=dre,
                    nivel1=nivel1,
                    nivel2=nivel2,
                    nivel3=nivel3,
                    nivel4=nivel4,
                    nivel5=nivel5,
                    is_analitica=is_analitica,
                )
                db.add(conta)
                created += 1
            else:
                conta.nome = nome
                conta.agrupamento_arvore = agrupamento
                conta.dre = dre
                updated += 1

        except Exception as e:
            errors.append(f"Linha {i}: {str(e)}")

    db.commit()

    return {
        "message": "Importação concluída.",
        "contas_criadas": created,
        "contas_atualizadas": updated,
        "erros": errors[:20],
    }


# ---------------------------------------------------------------------------
# 3. Importar Lançamentos (Budget ou Realizado/Razão)
# ---------------------------------------------------------------------------
# Colunas esperadas:
# Data de Lançamento | Nome Conta Contábil | Número Conta Contábil |
# Centro de Custo | Nome Conta Contra Partida | Fonte | Observ | Débito/Crédito (MC)

@router.post("/lancamentos", status_code=status.HTTP_200_OK)
def import_lancamentos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "financial"])),
):
    content = file.file.read()
    rows = parse_csv(content)
    if not rows:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou sem dados.")

    normalized = [{normalize_key(k): v.strip() for k, v in row.items()} for row in rows]

    created = 0
    skipped = 0
    errors = []

    DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]

    def parse_date(s: str) -> Optional[datetime.date]:
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    def parse_valor(s: str) -> Optional[Decimal]:
        s = s.replace("R$", "").strip()
        # Formato brasileiro: 1.234,56
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return Decimal(s)
        except InvalidOperation:
            return None

    for i, row in enumerate(normalized, start=2):
        try:
            # Data
            data_str = (
                row.get("data_de_lançamento")
                or row.get("data_de_lancamento")
                or row.get("data")
                or ""
            ).strip()
            data = parse_date(data_str)
            if not data:
                errors.append(f"Linha {i}: data inválida '{data_str}'.")
                skipped += 1
                continue

            # Número da conta
            numero_conta = (
                row.get("número_conta_contábil")
                or row.get("numero_conta_contabil")
                or row.get("número_conta")
                or ""
            ).strip()

            # Código do CC
            cc_cod = (row.get("centro_de_custo") or "").strip()

            # Valor
            valor_str = (
                row.get("débito_crédito_mc")
                or row.get("debito_credito_mc")
                or row.get("valor")
                or "0"
            ).strip()
            valor = parse_valor(valor_str)
            if valor is None:
                errors.append(f"Linha {i}: valor inválido '{valor_str}'.")
                skipped += 1
                continue

            # Fonte
            fonte = (row.get("fonte") or "Razão").strip()

            # Observação e contrapartida
            obs = (row.get("observ") or row.get("observacao") or "").strip() or None
            contrapartida = (
                row.get("nome_conta_contra_partida")
                or row.get("nome_conta_contrapartida")
                or ""
            ).strip() or None

            # Busca conta contábil
            conta = None
            if numero_conta:
                conta = db.query(ContaContabil).filter(ContaContabil.numero == numero_conta).first()
            if not conta:
                # Tenta pelo nome
                nome_conta = (
                    row.get("nome_conta_contábil")
                    or row.get("nome_conta_contabil")
                    or ""
                ).strip()
                if nome_conta:
                    conta = db.query(ContaContabil).filter(ContaContabil.nome == nome_conta).first()
            if not conta:
                errors.append(f"Linha {i}: conta contábil '{numero_conta}' não encontrada. Importe o plano de contas primeiro.")
                skipped += 1
                continue

            # Busca centro de custo
            cc = None
            if cc_cod:
                cc = db.query(CentroDeCusto).filter(CentroDeCusto.codigo == cc_cod).first()
            if not cc:
                errors.append(f"Linha {i}: centro de custo '{cc_cod}' não encontrado. Importe o dimensionamento primeiro.")
                skipped += 1
                continue

            lancamento = Lancamento(
                data_lancamento=data,
                conta_contabil_id=conta.id,
                centro_de_custo_id=cc.id,
                nome_conta_contrapartida=contrapartida,
                fonte=fonte,
                observacao=obs,
                valor=valor,
            )
            db.add(lancamento)
            created += 1

            # Commit em lotes de 1000 para performance
            if created % 1000 == 0:
                db.flush()

        except Exception as e:
            errors.append(f"Linha {i}: {str(e)}")
            skipped += 1

    db.commit()

    return {
        "message": "Importação concluída.",
        "lancamentos_criados": created,
        "lancamentos_ignorados": skipped,
        "erros": errors[:30],
    }


# ---------------------------------------------------------------------------
# Status / contagem
# ---------------------------------------------------------------------------

@router.get("/status")
def import_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "areas": db.query(Area).count(),
        "departamentos": db.query(Departamento).count(),
        "centros_de_custo": db.query(CentroDeCusto).count(),
        "contas_contabeis": db.query(ContaContabil).count(),
        "lancamentos": db.query(Lancamento).count(),
        "lancamentos_budget": db.query(Lancamento).filter(Lancamento.fonte == "Budget").count(),
        "lancamentos_razao": db.query(Lancamento).filter(Lancamento.fonte == "Razão").count(),
    }
