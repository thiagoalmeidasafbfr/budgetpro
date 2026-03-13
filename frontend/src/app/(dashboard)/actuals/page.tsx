"use client";

import { useState, useEffect, useCallback } from "react";
import { Download, Search, Calendar, FileSpreadsheet, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { lancamentosApi, type LancamentoItem } from "@/lib/api";

const FONTE_COLORS: Record<string, string> = {
  Budget: "bg-blue-100 text-blue-800",
  "Razão": "bg-emerald-100 text-emerald-800",
};

const MONTH_OPTIONS = [
  { value: "", label: "Todos os Meses" },
  { value: "1", label: "Janeiro" }, { value: "2", label: "Fevereiro" },
  { value: "3", label: "Março" }, { value: "4", label: "Abril" },
  { value: "5", label: "Maio" }, { value: "6", label: "Junho" },
  { value: "7", label: "Julho" }, { value: "8", label: "Agosto" },
  { value: "9", label: "Setembro" }, { value: "10", label: "Outubro" },
  { value: "11", label: "Novembro" }, { value: "12", label: "Dezembro" },
];

export default function ActualsPage() {
  const [year] = useState(2026);
  const [month, setMonth] = useState("");
  const [fonte, setFonte] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const [items, setItems] = useState<LancamentoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await lancamentosApi.list({
        year, month: month ? Number(month) : undefined,
        fonte: fonte || undefined, page, page_size: pageSize,
      });
      setItems(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar lançamentos");
    } finally {
      setLoading(false);
    }
  }, [year, month, fonte, page]);

  useEffect(() => { setPage(1); }, [month, fonte]);
  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = search
    ? items.filter((e) =>
        e.conta_contabil_nome.toLowerCase().includes(search.toLowerCase()) ||
        e.centro_de_custo_nome.toLowerCase().includes(search.toLowerCase()) ||
        (e.nome_conta_contrapartida ?? "").toLowerCase().includes(search.toLowerCase()) ||
        (e.observacao ?? "").toLowerCase().includes(search.toLowerCase())
      )
    : items;

  const totalValor = filtered.reduce((sum, e) => sum + Number(e.valor), 0);

  const handleExport = () => {
    const headers = ["Data", "Centro de Custo", "Conta Contábil", "Fonte", "Contrapartida", "Observação", "Valor"];
    const rows = filtered.map((e) => [
      e.data_lancamento,
      `${e.centro_de_custo_codigo} ${e.centro_de_custo_nome}`,
      `${e.conta_contabil_numero} ${e.conta_contabil_nome}`,
      e.fonte, e.nome_conta_contrapartida ?? "", e.observacao ?? "", e.valor.toString(),
    ]);
    const csv = [headers, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `lancamentos_${year}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Execução Orçamentária</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Lançamentos do razão e budget — {total.toLocaleString("pt-BR")} registros
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-accent transition-colors">
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} /> Atualizar
          </button>
          <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-accent transition-colors">
            <Download className="w-4 h-4" /> Exportar CSV
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <span>{error}</span>
          <button onClick={fetchData} className="ml-4 font-medium hover:underline flex items-center gap-1">
            <RefreshCw className="w-3.5 h-3.5" /> Tentar novamente
          </button>
        </div>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input type="text" placeholder="Buscar conta, centro, observação..." value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>
        <select value={fonte} onChange={(e) => setFonte(e.target.value)}
          className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          <option value="">Todas as Fontes</option>
          <option value="Budget">Budget</option>
          <option value="Razão">Razão</option>
        </select>
        <select value={month} onChange={(e) => setMonth(e.target.value)}
          className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          {MONTH_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div className="flex items-center gap-1 text-sm text-muted-foreground ml-auto">
          <FileSpreadsheet className="w-4 h-4" />
          {filtered.length} lançamentos |{" "}
          <span className="font-semibold text-foreground">{formatCurrency(totalValor)}</span>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                {["Data", "Centro de Custo", "Conta Contábil", "Contrapartida", "Observação", "Fonte", "Valor"].map((h) => (
                  <th key={h} className={cn("py-3 px-4 font-medium text-muted-foreground text-xs uppercase", h === "Valor" ? "text-right" : "text-left")}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-border">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="py-3 px-4"><div className="h-4 w-full animate-pulse rounded bg-muted" /></td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr><td colSpan={7} className="py-12 text-center text-muted-foreground">Nenhum lançamento encontrado.</td></tr>
              ) : (
                filtered.map((entry, idx) => (
                  <tr key={entry.id} className={cn("border-b border-border hover:bg-accent/50 transition-colors", idx % 2 === 0 ? "bg-card" : "bg-muted/20")}>
                    <td className="py-3 px-4 text-foreground whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                        {new Date(entry.data_lancamento + "T00:00:00").toLocaleDateString("pt-BR")}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs text-muted-foreground">{entry.centro_de_custo_codigo}</span>
                      <p className="font-medium text-foreground">{entry.centro_de_custo_nome}</p>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs text-muted-foreground">{entry.conta_contabil_numero}</span>
                      <p className="text-foreground">{entry.conta_contabil_nome}</p>
                    </td>
                    <td className="py-3 px-4 text-foreground max-w-[180px] truncate">{entry.nome_conta_contrapartida ?? "—"}</td>
                    <td className="py-3 px-4 text-muted-foreground max-w-[200px] truncate">{entry.observacao ?? "—"}</td>
                    <td className="py-3 px-4">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", FONTE_COLORS[entry.fonte] ?? "bg-gray-100 text-gray-800")}>
                        {entry.fonte}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-foreground whitespace-nowrap">{formatCurrency(Number(entry.valor))}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {pages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <p className="text-sm text-muted-foreground">Página {page} de {pages} — {total.toLocaleString("pt-BR")} registros</p>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent disabled:opacity-40 transition-colors">
                <ChevronLeft className="w-4 h-4" /> Anterior
              </button>
              <button onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page === pages}
                className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent disabled:opacity-40 transition-colors">
                Próximo <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
