"use client";

import { useState, useEffect } from "react";
import { Upload, CheckCircle, AlertCircle, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface StatusCarga {
  areas: number;
  departamentos: number;
  centros_de_custo: number;
  contas_contabeis: number;
  lancamentos_budget: number;
  lancamentos_razao: number;
  total_lancamentos: number;
}

interface ImportResult {
  mensagem: string;
  inseridos?: number;
  atualizados?: number;
  erros: string[];
}

interface StepProps {
  step: number;
  title: string;
  description: string;
  endpoint: string;
  countLabel: string;
  countValue: number | null;
  columns: string[];
  loading: boolean;
}

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

async function uploadFile(endpoint: string, file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const token = getToken();
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function ImportStep({ step, title, description, endpoint, countLabel, countValue, columns, loading }: StepProps) {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showColumns, setShowColumns] = useState(false);

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setError(null);
    setResult(null);
    try {
      const res = await uploadFile(endpoint, file);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro na importação");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
            {step}
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <div className="text-right">
          {loading ? (
            <div className="h-5 w-24 animate-pulse rounded bg-muted" />
          ) : (
            <span className="text-sm font-semibold text-foreground">
              {countValue !== null ? `${countValue.toLocaleString("pt-BR")} ${countLabel}` : "—"}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={() => setShowColumns(!showColumns)}
        className="flex items-center gap-1 text-xs text-primary hover:underline"
      >
        {showColumns ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        Ver colunas esperadas
      </button>

      {showColumns && (
        <div className="rounded-lg bg-muted/50 px-4 py-3">
          <p className="text-xs font-medium text-muted-foreground mb-1">Colunas do CSV (separado por ; ou ,):</p>
          <div className="flex flex-wrap gap-2">
            {columns.map((col) => (
              <code key={col} className="text-xs bg-background border border-border rounded px-2 py-0.5">{col}</code>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <label className="flex-1 cursor-pointer">
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(null); }}
          />
          <div className={cn(
            "flex items-center gap-2 rounded-lg border-2 border-dashed px-4 py-3 text-sm transition-colors",
            file ? "border-primary bg-primary/5 text-primary" : "border-border text-muted-foreground hover:border-primary/50"
          )}>
            <Upload className="w-4 h-4 shrink-0" />
            <span className="truncate">{file ? file.name : "Selecionar arquivo CSV"}</span>
          </div>
        </label>
        <button
          onClick={handleImport}
          disabled={!file || importing}
          className="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
        >
          {importing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          {importing ? "Importando..." : "Importar Arquivo"}
        </button>
      </div>

      {result && (
        <div className={cn(
          "rounded-lg border px-4 py-3 text-sm space-y-1",
          result.erros.length === 0
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : "border-amber-200 bg-amber-50 text-amber-800"
        )}>
          <div className="flex items-center gap-2 font-medium">
            {result.erros.length === 0 ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {result.mensagem}
          </div>
          {result.inseridos !== undefined && (
            <p className="text-xs">✓ {result.inseridos} inseridos {result.atualizados !== undefined ? `/ ${result.atualizados} atualizados` : ""}</p>
          )}
          {result.erros.length > 0 && (
            <div className="mt-2 space-y-1">
              <p className="text-xs font-medium">▼ {result.erros.length} erro(s):</p>
              {result.erros.map((e, i) => (
                <p key={i} className="text-xs font-mono">• {e}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          Erro na importação: {error}
        </div>
      )}
    </div>
  );
}

export default function CargaPage() {
  const [status, setStatus] = useState<StatusCarga | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  const fetchStatus = async () => {
    setStatusLoading(true);
    try {
      const token = getToken();
      const res = await fetch(`${BASE_URL}/importacao/status`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) setStatus(await res.json());
    } catch {}
    setStatusLoading(false);
  };

  useEffect(() => { fetchStatus(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Carga de Dados</h1>
          <p className="text-sm text-muted-foreground mt-1">Importe os dados na sequência correta</p>
        </div>
        <button
          onClick={fetchStatus}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-accent transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", statusLoading && "animate-spin")} /> Atualizar contagens
        </button>
      </div>

      <div className="space-y-4">
        <ImportStep
          step={1} title="Centros de Custo"
          description="Hierarquia: Área → Departamento → Centro de Custo"
          endpoint="/importacao/centros-de-custo"
          countLabel="centros de custo" countValue={status?.centros_de_custo ?? null}
          loading={statusLoading}
          columns={["Centro de Custo", "Nome do Centro de Custo", "Depart", "Nome Departamento", "Área", "Nome Área"]}
        />
        <ImportStep
          step={2} title="Plano de Contas"
          description="Contas contábeis com agrupamento e classificação DRE"
          endpoint="/importacao/plano-de-contas"
          countLabel="contas contábeis" countValue={status?.contas_contabeis ?? null}
          loading={statusLoading}
          columns={["Número Conta Contábil", "Nome Conta Contábil", "Agrupamento Arvore", "DRE"]}
        />
        <ImportStep
          step={3} title="Lançamentos (Budget / Razão)"
          description="Débitos e créditos do razão contábil e do budget"
          endpoint="/importacao/lancamentos"
          countLabel="lançamentos" countValue={status?.total_lancamentos ?? null}
          loading={statusLoading}
          columns={["Data de Lançamento", "Número Conta Contábil", "Nome Conta Contábil", "Centro de Custo", "Nome Conta Contra Partida", "Fonte", "Observ", "Débito/ Crédito (MC)"]}
        />
      </div>

      {status && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h3 className="font-semibold text-foreground mb-4">Resumo da Base de Dados</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {[
              { label: "Áreas", value: status.areas },
              { label: "Departamentos", value: status.departamentos },
              { label: "Centros de Custo", value: status.centros_de_custo },
              { label: "Contas Contábeis", value: status.contas_contabeis },
              { label: "Budget", value: status.lancamentos_budget },
              { label: "Razão", value: status.lancamentos_razao },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-lg bg-muted/50 p-3 text-center">
                <p className="text-lg font-bold text-foreground">{value.toLocaleString("pt-BR")}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
