import csv
import io
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Area, Departamento, CentroDeCusto, ContaContabil, Lancamento

router = APIRouter(prefix="/api/importacao", tags=["importacao"])


def parse_valor(valor_str: str) -> float:
    """Converte string de valor brasileiro (14.768.437,20) para float."""
    if not valor_str or valor_str.strip() in ("-", ""):
        return 0.0
    cleaned = valor_str.strip().replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_data(data_str: str):
    """Converte data no formato DD/MM/YYYY para objeto date."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(data_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de data não reconhecido: {data_str}")


@router.post("/centros-de-custo")
async def importar_centros_de_custo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa a planilha de Dimensionamento de Centros de Custo.
    Colunas esperadas (separadas por ; ou ,):
    Centro de Custo | Nome do Centro de Custo | Depart | Nome Departamento | Área | Nome Área
    """
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # utf-8-sig para remover BOM do Excel
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Detecta delimitador
    delimiter = ";"
    if text.count(",") > text.count(";"):
        delimiter = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    inseridos = 0
    atualizados = 0
    erros = []

    for i, row in enumerate(reader, start=2):
        try:
            # Normaliza nomes de colunas (remove espaços extras)
            row = {k.strip(): v.strip() for k, v in row.items() if k}

            codigo_area = row.get("Área") or row.get("Area") or ""
            nome_area = row.get("Nome Área") or row.get("Nome Area") or ""
            codigo_depart = row.get("Depart") or ""
            nome_depart = row.get("Nome Departamento") or ""
            codigo_cc = row.get("Centro de Custo") or ""
            nome_cc = row.get("Nome do Centro de Custo") or ""

            if not codigo_cc:
                continue

            # Upsert Area
            area = db.query(Area).filter(Area.codigo == codigo_area).first()
            if not area:
                area = Area(codigo=codigo_area, nome=nome_area)
                db.add(area)
                db.flush()
            elif area.nome != nome_area:
                area.nome = nome_area

            # Upsert Departamento
            depart = db.query(Departamento).filter(Departamento.codigo == codigo_depart).first()
            if not depart:
                depart = Departamento(codigo=codigo_depart, nome=nome_depart, area_id=area.id)
                db.add(depart)
                db.flush()
            elif depart.nome != nome_depart:
                depart.nome = nome_depart

            # Upsert Centro de Custo
            cc = db.query(CentroDeCusto).filter(CentroDeCusto.codigo == codigo_cc).first()
            if not cc:
                cc = CentroDeCusto(codigo=codigo_cc, nome=nome_cc, departamento_id=depart.id)
                db.add(cc)
                inseridos += 1
            else:
                cc.nome = nome_cc
                cc.departamento_id = depart.id
                atualizados += 1

        except Exception as e:
            erros.append(f"Linha {i}: {str(e)}")

    db.commit()
    return {
        "mensagem": "Importação concluída",
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros[:20]  # limita a 20 erros no retorno
    }


@router.post("/plano-de-contas")
async def importar_plano_de_contas(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa o Plano de Contas.
    Colunas esperadas:
    Número Conta Contábil | Nome Conta Contábil | Agrupamento Arvore | DRE
    """
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    delimiter = ";"
    if text.count(",") > text.count(";"):
        delimiter = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    inseridos = 0
    atualizados = 0
    erros = []

    for i, row in enumerate(reader, start=2):
        try:
            row = {k.strip(): v.strip() for k, v in row.items() if k}

            numero = row.get("Número Conta Contábil") or row.get("Numero Conta Contabil") or ""
            nome = row.get("Nome Conta Contábil") or row.get("Nome Conta Contabil") or ""
            agrupamento = row.get("Agrupamento Arvore") or ""
            dre = row.get("DRE") or ""

            if not numero:
                continue

            # Deriva os níveis hierárquicos do número da conta
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
                    is_analitica=is_analitica
                )
                db.add(conta)
                inseridos += 1
            else:
                conta.nome = nome
                conta.agrupamento_arvore = agrupamento
                conta.dre = dre
                conta.nivel1 = nivel1
                conta.nivel2 = nivel2
                conta.nivel3 = nivel3
                conta.nivel4 = nivel4
                conta.nivel5 = nivel5
                atualizados += 1

        except Exception as e:
            erros.append(f"Linha {i}: {str(e)}")

    db.commit()
    return {
        "mensagem": "Importação concluída",
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros[:20]
    }


@router.post("/lancamentos")
async def importar_lancamentos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa lançamentos de Budget ou Realizado/Razão.
    Colunas esperadas:
    Data de Lançamento | Nome Conta Contábil | Número Conta Contábil | Centro de Custo
    | Nome Conta Contra Partida | Fonte | Observ | Débito/ Crédito (MC)
    """
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    delimiter = ";"
    if text.count(",") > text.count(";"):
        delimiter = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    inseridos = 0
    erros = []

    # Cache para evitar múltiplas queries por conta/cc
    cache_contas = {}
    cache_cc = {}

    for i, row in enumerate(reader, start=2):
        try:
            row = {k.strip(): v.strip() for k, v in row.items() if k}

            data_str = row.get("Data de Lançamento") or row.get("Data de Lancamento") or ""
            numero_conta = row.get("Número Conta Contábil") or row.get("Numero Conta Contabil") or ""
            codigo_cc = row.get("Centro de Custo") or ""
            nome_contrapartida = row.get("Nome Conta Contra Partida") or row.get("Nome Com") or ""
            fonte = row.get("Fonte") or ""
            observacao = row.get("Observ") or row.get("Observação") or ""
            valor_str = row.get("Débito/ Crédito (MC)") or row.get("Debito/ Credito (MC)") or "0"

            if not data_str or not numero_conta or not codigo_cc:
                continue

            data = parse_data(data_str)
            valor = parse_valor(valor_str)

            # Busca conta contábil (com cache)
            if numero_conta not in cache_contas:
                conta = db.query(ContaContabil).filter(ContaContabil.numero == numero_conta).first()
                if not conta:
                    # Cria a conta automaticamente se não existir
                    partes = numero_conta.split(".")
                    conta = ContaContabil(
                        numero=numero_conta,
                        nome=row.get("Nome Conta Contábil") or row.get("Nome Conta Contabil") or numero_conta,
                        nivel1=partes[0] if len(partes) >= 1 else None,
                        nivel2=".".join(partes[:2]) if len(partes) >= 2 else None,
                        nivel3=".".join(partes[:3]) if len(partes) >= 3 else None,
                        nivel4=".".join(partes[:4]) if len(partes) >= 4 else None,
                        nivel5=numero_conta if len(partes) >= 5 else None,
                        is_analitica=len(partes) >= 5
                    )
                    db.add(conta)
                    db.flush()
                cache_contas[numero_conta] = conta
            conta = cache_contas[numero_conta]

            # Busca centro de custo (com cache)
            if codigo_cc not in cache_cc:
                cc = db.query(CentroDeCusto).filter(CentroDeCusto.codigo == codigo_cc).first()
                if not cc:
                    # Cria área/departamento/cc padrão se não existir
                    area_default = db.query(Area).filter(Area.codigo == "IMPORT").first()
                    if not area_default:
                        area_default = Area(codigo="IMPORT", nome="Importado")
                        db.add(area_default)
                        db.flush()
                    depart_default = db.query(Departamento).filter(Departamento.codigo == "IMPORT").first()
                    if not depart_default:
                        depart_default = Departamento(codigo="IMPORT", nome="Importado", area_id=area_default.id)
                        db.add(depart_default)
                        db.flush()
                    cc = CentroDeCusto(codigo=codigo_cc, nome=codigo_cc, departamento_id=depart_default.id)
                    db.add(cc)
                    db.flush()
                cache_cc[codigo_cc] = cc
            cc = cache_cc[codigo_cc]

            lancamento = Lancamento(
                data_lancamento=data,
                conta_contabil_id=conta.id,
                centro_de_custo_id=cc.id,
                nome_conta_contrapartida=nome_contrapartida,
                fonte=fonte,
                observacao=observacao if observacao != "-" else None,
                valor=valor
            )
            db.add(lancamento)
            inseridos += 1

            # Commit em lotes de 1000 para performance
            if inseridos % 1000 == 0:
                db.commit()

        except Exception as e:
            erros.append(f"Linha {i}: {str(e)}")

    db.commit()
    return {
        "mensagem": "Importação concluída",
        "inseridos": inseridos,
        "erros": erros[:20]
    }


@router.get("/status")
def status_carga(db: Session = Depends(get_db)):
    """Retorna o status atual da carga de dados."""
    return {
        "areas": db.query(Area).count(),
        "departamentos": db.query(Departamento).count(),
        "centros_de_custo": db.query(CentroDeCusto).count(),
        "contas_contabeis": db.query(ContaContabil).count(),
        "lancamentos_budget": db.query(Lancamento).filter(Lancamento.fonte == "Budget").count(),
        "lancamentos_razao": db.query(Lancamento).filter(Lancamento.fonte == "Razão").count(),
        "total_lancamentos": db.query(Lancamento).count(),
    }
