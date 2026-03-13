"use client";

import { useState } from "react";
import { Upload, CheckCircle, AlertCircle, Loader2, Database, FileSpreadsheet } from "lucide-react";

const API_BASE = "/backend";

type TipoImportacao = "centros-de-custo" | "plano-de-contas" | "lancamentos";

interface StatusCarga {
  areas: number;
  departamentos: number;
  centros_de_custo: number;
  contas_contabeis: number;
  lancamentos_budget: number;
  lancamentos_razao: number;
  total_lancamentos: number;
}

interface ResultadoImportacao {
  mensagem: string;
  inseridos: number;
  atualizados?: number;
  erros: string[];
}

const TIPOS: { key: TipoImportacao; label: string; descricao: string; colunas: string }[] = [
  {
    key: "centros-de-custo",
    label: "Dimensionamento de Centros de Custo",
    descricao: "Planilha com a hierarquia Área → Departamento → Centro de Custo",
    colunas: "Centro de Custo | Nome do Centro de Custo | Depart | Nome Departamento | Área | Nome Área",
  },
  {
    key: "plano-de-contas",
    label: "Plano de Contas",
    descricao: "Planilha com o plano de contas e sua hierarquia de 5 níveis",
    colunas: "Número Conta Contábil | Nome Conta Contábil | Agrupamento Arvore | DRE",
  },
  {
    key: "lancamentos",
    label: "Lançamentos (Budget ou Realizado)",
    descricao: "Planilha de budget ou razão — a coluna Fonte diferencia os registros",
    colunas: "Data de Lançamento | Nome Conta Contábil | Número Conta Contábil | Centro de Custo | Nome Conta Contra Partida | Fonte | Observ | Débito/ Crédito (MC)",
  },
];

export default function CargaDados() {
  const [tipo, setTipo] = useState<TipoImportacao>("centros-de-custo");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusCarga | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  const tipoAtual = TIPOS.find((t) => t.key === tipo)!;

  const carregarStatus = async () => {
    setLoadingStatus(true);
    try {
      const res = await fetch(`${API_BASE}/api/importacao/status`);
      if (res.ok) setStatus(await res.json());
    } catch {
      // backend pode estar offline
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleImportar = async () => {
    if (!file) return;
    setLoading(true);
    setResultado(null);
    setErro(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/importacao/${tipo}`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`Erro HTTP ${res.status}`);
      const data = await res.json();
      setResultado(data);
      carregarStatus();
    } catch (e: any) {
      setErro(e.message || "Erro ao importar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Carga de Dados</h1>
        <p className="text-gray-500 mt-1">Importe suas planilhas do Excel (salvas como CSV) para o sistema</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-gray-700">Status do Banco de Dados</span>
          </div>
          <button
            onClick={carregarStatus}
            disabled={loadingStatus}
            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
          >
            {loadingStatus ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
            Atualizar
          </button>
        </div>
        {status ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-800">{status.centros_de_custo.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">Centros de Custo</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-800">{status.contas_contabeis.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">Contas Contábeis</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-600">{status.lancamentos_budget.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">Lançamentos Budget</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600">{status.lancamentos_razao.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">Lançamentos Razão</div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">Clique em &quot;Atualizar&quot; para ver os dados do banco (requer backend rodando)</p>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <p className="text-sm font-medium text-gray-700 mb-3">1. Selecione o tipo de importação</p>
        <div className="flex flex-col gap-2">
          {TIPOS.map((t) => (
            <label
              key={t.key}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                tipo === t.key ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <input
                type="radio"
                name="tipo"
                value={t.key}
                checked={tipo === t.key}
                onChange={() => { setTipo(t.key); setFile(null); setResultado(null); setErro(null); }}
                className="mt-1"
              />
              <div>
                <div className="font-medium text-gray-800">{t.label}</div>
                <div className="text-sm text-gray-500">{t.descricao}</div>
                <div className="text-xs text-gray-400 mt-1 font-mono">{t.colunas}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <p className="text-sm font-medium text-gray-700 mb-3">2. Selecione o arquivo CSV</p>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
          <FileSpreadsheet className="w-10 h-10 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-500 mb-2">
            Salve sua planilha Excel como <strong>CSV (separado por ponto e vírgula)</strong> antes de importar
          </p>
          <input
            type="file"
            accept=".csv,.txt"
            onChange={(e) => { setFile(e.target.files?.[0] || null); setResultado(null); setErro(null); }}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors text-sm"
          >
            Escolher arquivo
          </label>
          {file && (
            <p className="mt-2 text-sm text-green-600 font-medium">✓ {file.name} ({(file.size / 1024).toFixed(0)} KB)</p>
          )}
        </div>
      </div>

      <button
        onClick={handleImportar}
        disabled={!file || loading}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <><Loader2 className="w-5 h-5 animate-spin" /> Importando...</>
        ) : (
          <><Upload className="w-5 h-5" /> Importar {tipoAtual.label}</>
        )}
      </button>

      {resultado && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-green-700">{resultado.mensagem}</span>
          </div>
          <div className="text-sm text-green-600">
            <span>✓ {resultado.inseridos} registros inseridos</span>
            {resultado.atualizados !== undefined && (
              <span className="ml-4">↻ {resultado.atualizados} registros atualizados</span>
            )}
          </div>
          {resultado.erros.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-medium text-amber-700">Avisos ({resultado.erros.length} linhas com problema):</p>
              <ul className="text-xs text-amber-600 mt-1 space-y-1">
                {resultado.erros.map((e, i) => <li key={i}>• {e}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {erro && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{erro}</span>
        </div>
      )}

      <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
        <p className="text-sm font-semibold text-amber-800 mb-2">📋 Como exportar do Excel para CSV</p>
        <ol className="text-sm text-amber-700 space-y-1 list-decimal list-inside">
          <li>Abra sua planilha no Excel</li>
          <li>Clique em <strong>Arquivo → Salvar Como</strong></li>
          <li>Escolha o formato <strong>CSV UTF-8 (delimitado por vírgula)</strong> ou <strong>CSV (separado por ponto e vírgula)</strong></li>
          <li>Certifique-se de que a <strong>primeira linha contém os nomes das colunas</strong></li>
          <li>Salve e faça o upload aqui</li>
        </ol>
      </div>
    </div>
  );
}
