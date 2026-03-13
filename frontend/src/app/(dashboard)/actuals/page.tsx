"use client";

import { useState } from "react";
import {
  Upload,
  Download,
  Search,
  Calendar,
  Filter,
  Plus,
  FileSpreadsheet,
} from "lucide-react";
import { formatCurrency, cn, getVarianceColor } from "@/lib/utils";

interface ActualEntry {
  id: string;
  date: string;
  costCenterCode: string;
  costCenterName: string;
  accountCode: string;
  accountName: string;
  category: string;
  vendor: string;
  amount: number;
  description: string;
  source: string;
}

const MOCK_ACTUALS: ActualEntry[] = [
  { id: "1", date: "2026-03-28", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", vendor: "Folha de Pagamento", amount: 122000, description: "Folha março/2026", source: "erp" },
  { id: "2", date: "2026-03-25", costCenterCode: "CC005", costCenterName: "Desenvolvimento", accountCode: "6.1.01", accountName: "Licenças de Software", category: "investment", vendor: "Microsoft", amount: 48500, description: "Azure + M365 licenças", source: "erp" },
  { id: "3", date: "2026-03-20", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.06", accountName: "Viagens e Hospedagem", category: "expense", vendor: "CVC Corporate", amount: 42000, description: "Viagens equipe comercial", source: "manual" },
  { id: "4", date: "2026-03-18", costCenterCode: "CC005", costCenterName: "Desenvolvimento", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", vendor: "Folha de Pagamento", amount: 185000, description: "Folha março/2026 - Dev", source: "erp" },
  { id: "5", date: "2026-03-15", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "3.1.01", accountName: "Receita de Vendas Nacionais", category: "revenue", vendor: "Clientes Diversos", amount: 920000, description: "Receita vendas março", source: "erp" },
  { id: "6", date: "2026-03-12", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.07", accountName: "Marketing e Publicidade", category: "expense", vendor: "Agência XYZ", amount: 62000, description: "Campanha Q1", source: "manual" },
  { id: "7", date: "2026-03-10", costCenterCode: "CC006", costCenterName: "Infraestrutura TI", accountCode: "5.1.04", accountName: "Energia e Telecom", category: "expense", vendor: "Algar Telecom", amount: 18500, description: "Link dedicado + telefonia", source: "erp" },
  { id: "8", date: "2026-03-05", costCenterCode: "CC005", costCenterName: "Desenvolvimento", accountCode: "6.1.02", accountName: "Equipamentos de TI", category: "investment", vendor: "Dell Technologies", amount: 35000, description: "Notebooks desenvolvedores", source: "excel" },
  { id: "9", date: "2026-03-01", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "5.1.03", accountName: "Aluguel e Condomínio", category: "expense", vendor: "Imobiliária Central", amount: 18000, description: "Aluguel sede março", source: "erp" },
  { id: "10", date: "2026-02-28", costCenterCode: "CC007", costCenterName: "Recrutamento", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", vendor: "Folha de Pagamento", amount: 65000, description: "Folha fevereiro/2026 - RH", source: "erp" },
  { id: "11", date: "2026-02-25", costCenterCode: "CC004", costCenterName: "Vendas Internacionais", accountCode: "5.1.06", accountName: "Viagens e Hospedagem", category: "expense", vendor: "Latam Airlines", amount: 38000, description: "Viagem Miami - Feira", source: "manual" },
  { id: "12", date: "2026-02-20", costCenterCode: "CC002", costCenterName: "Contabilidade", accountCode: "5.1.08", accountName: "Consultoria e Assessoria", category: "expense", vendor: "PwC", amount: 75000, description: "Auditoria externa Q1", source: "manual" },
  { id: "13", date: "2026-02-15", costCenterCode: "CC008", costCenterName: "Treinamento", accountCode: "5.1.02", accountName: "Benefícios", category: "expense", vendor: "Alelo", amount: 42000, description: "VR + VA fevereiro", source: "erp" },
  { id: "14", date: "2026-01-30", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "3.1.01", accountName: "Receita de Vendas Nacionais", category: "revenue", vendor: "Clientes Diversos", amount: 850000, description: "Receita vendas janeiro", source: "erp" },
  { id: "15", date: "2026-01-15", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.07", accountName: "Marketing e Publicidade", category: "expense", vendor: "Google Ads", amount: 55000, description: "Campanha digital janeiro", source: "api" },
];

const BUDGET_COMPARISON = [
  { month: "Jan", budget: 1200000, actual: 1150000 },
  { month: "Fev", budget: 1300000, actual: 1380000 },
  { month: "Mar", budget: 1350000, actual: 1420000 },
];

const categoryColors: Record<string, string> = {
  revenue: "bg-green-100 text-green-800",
  cost: "bg-red-100 text-red-800",
  expense: "bg-amber-100 text-amber-800",
  investment: "bg-purple-100 text-purple-800",
};

const categoryLabels: Record<string, string> = {
  revenue: "Receita",
  cost: "Custo",
  expense: "Despesa",
  investment: "Investimento",
};

const sourceLabels: Record<string, string> = {
  erp: "ERP",
  manual: "Manual",
  excel: "Excel",
  api: "API",
};

export default function ActualsPage() {
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterMonth, setFilterMonth] = useState("");

  const filtered = MOCK_ACTUALS.filter((entry) => {
    const matchesSearch =
      !search ||
      entry.accountName.toLowerCase().includes(search.toLowerCase()) ||
      entry.costCenterName.toLowerCase().includes(search.toLowerCase()) ||
      entry.vendor.toLowerCase().includes(search.toLowerCase()) ||
      entry.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      !filterCategory || entry.category === filterCategory;
    const matchesMonth =
      !filterMonth || entry.date.startsWith(`2026-${filterMonth}`);
    return matchesSearch && matchesCategory && matchesMonth;
  });

  const totalActual = filtered.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Execução Orçamentária
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Acompanhamento dos valores realizados vs orçamento
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-accent transition-colors">
            <Upload className="w-4 h-4" />
            Importar
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-accent transition-colors">
            <Download className="w-4 h-4" />
            Exportar
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Novo Lançamento
          </button>
        </div>
      </div>

      {/* Budget vs Actual Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {BUDGET_COMPARISON.map((item) => {
          const variance = item.budget - item.actual;
          const variancePct = ((variance / item.budget) * 100).toFixed(1);
          return (
            <div
              key={item.month}
              className="rounded-xl border border-border bg-card p-4 shadow-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">
                  {item.month} 2026
                </span>
                <span
                  className={cn(
                    "text-xs font-medium px-2 py-0.5 rounded-full",
                    variance >= 0
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  )}
                >
                  {variance >= 0 ? "Dentro" : "Acima"} ({variancePct}%)
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Orçado</p>
                  <p className="text-sm font-semibold">
                    {formatCurrency(item.budget)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Realizado</p>
                  <p className="text-sm font-semibold">
                    {formatCurrency(item.actual)}
                  </p>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-3 w-full bg-muted rounded-full h-2">
                <div
                  className={cn(
                    "h-2 rounded-full transition-all",
                    item.actual <= item.budget ? "bg-emerald-500" : "bg-red-500"
                  )}
                  style={{
                    width: `${Math.min((item.actual / item.budget) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar por conta, centro de custo, fornecedor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Todas Categorias</option>
          <option value="revenue">Receita</option>
          <option value="cost">Custo</option>
          <option value="expense">Despesa</option>
          <option value="investment">Investimento</option>
        </select>
        <select
          value={filterMonth}
          onChange={(e) => setFilterMonth(e.target.value)}
          className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Todos os Meses</option>
          <option value="01">Janeiro</option>
          <option value="02">Fevereiro</option>
          <option value="03">Março</option>
        </select>
        <div className="flex items-center gap-1 text-sm text-muted-foreground ml-auto">
          <FileSpreadsheet className="w-4 h-4" />
          {filtered.length} lançamentos | Total:{" "}
          <span className="font-semibold text-foreground">
            {formatCurrency(totalActual)}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Data
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Centro de Custo
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Conta Contábil
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Categoria
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Fornecedor
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Descrição
                </th>
                <th className="text-right py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Valor
                </th>
                <th className="text-center py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Origem
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry, idx) => (
                <tr
                  key={entry.id}
                  className={cn(
                    "border-b border-border hover:bg-accent/50 transition-colors cursor-pointer",
                    idx % 2 === 0 ? "bg-card" : "bg-muted/20"
                  )}
                >
                  <td className="py-3 px-4 text-foreground whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                      {new Date(entry.date).toLocaleDateString("pt-BR")}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <span className="text-xs text-muted-foreground">
                        {entry.costCenterCode}
                      </span>
                      <p className="font-medium text-foreground">
                        {entry.costCenterName}
                      </p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <span className="text-xs text-muted-foreground">
                        {entry.accountCode}
                      </span>
                      <p className="text-foreground">{entry.accountName}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={cn(
                        "text-xs px-2 py-0.5 rounded-full font-medium",
                        categoryColors[entry.category]
                      )}
                    >
                      {categoryLabels[entry.category]}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-foreground">
                    {entry.vendor}
                  </td>
                  <td className="py-3 px-4 text-muted-foreground max-w-[200px] truncate">
                    {entry.description}
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-foreground whitespace-nowrap">
                    {formatCurrency(entry.amount)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-xs bg-muted px-2 py-0.5 rounded font-medium text-muted-foreground">
                      {sourceLabels[entry.source]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
