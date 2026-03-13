"use client";

import { useState } from "react";
import {
  TrendingUp,
  Play,
  RefreshCw,
  Info,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { formatCurrency, cn, MONTHS } from "@/lib/utils";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const MONTH_KEYS = [
  "jan", "feb", "mar", "apr", "may", "jun",
  "jul", "aug", "sep", "oct", "nov", "dec",
] as const;

interface ForecastRow {
  id: string;
  costCenterCode: string;
  costCenterName: string;
  accountCode: string;
  accountName: string;
  category: string;
  method: string;
  months: number[];
  total: number;
  budgetTotal: number;
}

const MOCK_FORECAST: ForecastRow[] = [
  { id: "1", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", method: "linear", months: [120000, 121500, 122000, 121167, 121167, 121167, 121167, 121167, 121167, 121167, 121167, 121167], total: 1454902, budgetTotal: 1495000 },
  { id: "2", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "5.1.03", accountName: "Aluguel e Condomínio", category: "expense", method: "linear", months: [18000, 18000, 18200, 18067, 18067, 18067, 18067, 18067, 18067, 18067, 18067, 18067], total: 216803, budgetTotal: 216000 },
  { id: "3", costCenterCode: "CC001", costCenterName: "Tesouraria", accountCode: "3.1.01", accountName: "Receita de Vendas", category: "revenue", method: "historical", months: [850000, 920000, 880000, 950000, 1100000, 1050000, 980000, 1020000, 1080000, 1150000, 1200000, 1350000], total: 12530000, budgetTotal: 12530000 },
  { id: "4", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", method: "linear", months: [95000, 96000, 97000, 96000, 96000, 96000, 96000, 96000, 96000, 96000, 96000, 96000], total: 1152000, budgetTotal: 1184000 },
  { id: "5", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.06", accountName: "Viagens e Hospedagem", category: "expense", method: "linear", months: [35000, 28000, 42000, 35000, 35000, 35000, 35000, 35000, 35000, 35000, 35000, 35000], total: 420000, budgetTotal: 444000 },
  { id: "6", costCenterCode: "CC003", costCenterName: "Vendas Nacionais", accountCode: "5.1.07", accountName: "Marketing e Publicidade", category: "expense", method: "linear", months: [65000, 55000, 62000, 60667, 60667, 60667, 60667, 60667, 60667, 60667, 60667, 60667], total: 722001, budgetTotal: 790000 },
  { id: "7", costCenterCode: "CC005", costCenterName: "Desenvolvimento", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", method: "linear", months: [180000, 182000, 185000, 182333, 182333, 182333, 182333, 182333, 182333, 182333, 182333, 182333], total: 2187996, budgetTotal: 2270000 },
  { id: "8", costCenterCode: "CC005", costCenterName: "Desenvolvimento", accountCode: "6.1.01", accountName: "Licenças de Software", category: "investment", method: "linear", months: [45000, 46000, 45500, 45500, 45500, 45500, 45500, 45500, 45500, 45500, 45500, 45500], total: 546000, budgetTotal: 561000 },
  { id: "9", costCenterCode: "CC006", costCenterName: "Infraestrutura TI", accountCode: "5.1.04", accountName: "Energia e Telecom", category: "expense", method: "linear", months: [18000, 18500, 19000, 18500, 18500, 18500, 18500, 18500, 18500, 18500, 18500, 18500], total: 222000, budgetTotal: 228000 },
  { id: "10", costCenterCode: "CC007", costCenterName: "Recrutamento", accountCode: "5.1.01", accountName: "Salários e Encargos", category: "expense", method: "manual", months: [65000, 65000, 67000, 68000, 68000, 70000, 70000, 70000, 72000, 72000, 72000, 75000], total: 834000, budgetTotal: 840000 },
];

const chartData = MONTHS.map((month, idx) => {
  const budgetVals = [1200000, 1300000, 1350000, 1250000, 1400000, 1350000, 1300000, 1350000, 1250000, 1300000, 1400000, 1500000];
  const actualVals = [1150000, 1280000, 1420000, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  const forecastVals = [1150000, 1280000, 1420000, 1283333, 1283333, 1283333, 1283333, 1283333, 1283333, 1283333, 1283333, 1283333];

  return {
    month,
    budget: budgetVals[idx],
    actual: idx < 3 ? actualVals[idx] : null,
    forecast: forecastVals[idx],
  };
});

const methodLabels: Record<string, string> = {
  linear: "Linear",
  historical: "Histórico",
  manual: "Manual",
};

const methodColors: Record<string, string> = {
  linear: "bg-blue-100 text-blue-800",
  historical: "bg-purple-100 text-purple-800",
  manual: "bg-gray-100 text-gray-800",
};

const categoryColors: Record<string, string> = {
  revenue: "bg-green-100 text-green-800",
  expense: "bg-amber-100 text-amber-800",
  investment: "bg-purple-100 text-purple-800",
};

const categoryLabels: Record<string, string> = {
  revenue: "Receita",
  cost: "Custo",
  expense: "Despesa",
  investment: "Investimento",
};

const fmtCompact = (v: number) => {
  if (Math.abs(v) >= 1e6) return `R$ ${(v / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e3) return `R$ ${(v / 1e3).toFixed(0)}K`;
  return `R$ ${v}`;
};

export default function ForecastPage() {
  const [method, setMethod] = useState("linear");
  const currentMonth = 3; // March

  const totalForecast = MOCK_FORECAST.reduce((s, r) => s + r.total, 0);
  const totalBudget = MOCK_FORECAST.reduce((s, r) => s + r.budgetTotal, 0);
  const variance = totalBudget - totalForecast;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Forecast</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Projeção financeira: Realizado até Mar/2026 + Projeção Abr-Dez
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="linear">Método: Linear</option>
            <option value="historical">Método: Histórico</option>
            <option value="manual">Método: Manual</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
            <Play className="w-4 h-4" />
            Gerar Forecast
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Forecast Anual
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {fmtCompact(totalForecast)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Orçamento Anual
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {fmtCompact(totalBudget)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Desvio Projetado
          </p>
          <div className="flex items-center gap-2 mt-1">
            <p
              className={cn(
                "text-2xl font-bold",
                variance >= 0 ? "text-green-600" : "text-red-600"
              )}
            >
              {fmtCompact(Math.abs(variance))}
            </p>
            {variance >= 0 ? (
              <ArrowDownRight className="w-5 h-5 text-green-600" />
            ) : (
              <ArrowUpRight className="w-5 h-5 text-red-600" />
            )}
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Meses Realizados
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {currentMonth} / 12
          </p>
          <div className="mt-2 w-full bg-muted rounded-full h-2">
            <div
              className="h-2 rounded-full bg-primary"
              style={{ width: `${(currentMonth / 12) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-foreground mb-4">
          Orçado vs Realizado vs Forecast
        </h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => fmtCompact(v)} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: unknown) => formatCurrency(Number(value))}
                labelStyle={{ fontWeight: 600 }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="budget"
                name="Orçado"
                stroke="#3b82f6"
                fill="#3b82f680"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="forecast"
                name="Forecast"
                stroke="#8b5cf6"
                fill="#8b5cf640"
                strokeWidth={2}
                strokeDasharray="5 5"
              />
              <Area
                type="monotone"
                dataKey="actual"
                name="Realizado"
                stroke="#10b981"
                fill="#10b98160"
                strokeWidth={2}
                connectNulls={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Forecast Table */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase sticky left-0 bg-muted/50 z-10">
                  Centro de Custo
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase sticky left-[180px] bg-muted/50 z-10">
                  Conta
                </th>
                <th className="text-center py-3 px-3 font-medium text-muted-foreground text-xs uppercase">
                  Método
                </th>
                {MONTHS.map((m) => (
                  <th
                    key={m}
                    className="text-right py-3 px-3 font-medium text-muted-foreground text-xs uppercase min-w-[100px]"
                  >
                    {m}
                  </th>
                ))}
                <th className="text-right py-3 px-4 font-medium text-muted-foreground text-xs uppercase bg-muted/30">
                  Total
                </th>
                <th className="text-right py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                  Desvio
                </th>
              </tr>
            </thead>
            <tbody>
              {MOCK_FORECAST.map((row, idx) => {
                const dev = row.budgetTotal - row.total;
                const devPct =
                  row.budgetTotal > 0
                    ? ((dev / row.budgetTotal) * 100).toFixed(1)
                    : "0";
                return (
                  <tr
                    key={row.id}
                    className={cn(
                      "border-b border-border hover:bg-accent/50 transition-colors",
                      idx % 2 === 0 ? "bg-card" : "bg-muted/20"
                    )}
                  >
                    <td className="py-2.5 px-4 sticky left-0 bg-inherit z-10">
                      <span className="text-xs text-muted-foreground">
                        {row.costCenterCode}
                      </span>
                      <p className="font-medium text-foreground text-xs">
                        {row.costCenterName}
                      </p>
                    </td>
                    <td className="py-2.5 px-4 sticky left-[180px] bg-inherit z-10">
                      <span className="text-xs text-muted-foreground">
                        {row.accountCode}
                      </span>
                      <p className="text-xs text-foreground">
                        {row.accountName}
                      </p>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={cn(
                          "text-xs px-2 py-0.5 rounded-full font-medium",
                          methodColors[row.method]
                        )}
                      >
                        {methodLabels[row.method]}
                      </span>
                    </td>
                    {row.months.map((val, mIdx) => (
                      <td
                        key={mIdx}
                        className={cn(
                          "py-2.5 px-3 text-right text-xs whitespace-nowrap",
                          mIdx < currentMonth
                            ? "text-foreground font-medium"
                            : "text-muted-foreground italic"
                        )}
                      >
                        {formatCurrency(val)}
                      </td>
                    ))}
                    <td className="py-2.5 px-4 text-right font-semibold text-foreground text-xs bg-muted/30 whitespace-nowrap">
                      {formatCurrency(row.total)}
                    </td>
                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                      <span
                        className={cn(
                          "text-xs font-medium",
                          dev >= 0 ? "text-green-600" : "text-red-600"
                        )}
                      >
                        {dev >= 0 ? "+" : ""}
                        {devPct}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info box */}
      <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-50 border border-blue-200">
        <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Como funciona o Forecast</p>
          <p className="mt-1 text-blue-700">
            <strong>Linear:</strong> Média dos meses realizados projetada para
            os meses restantes. <strong>Histórico:</strong> Usa valores do mesmo
            mês no ano anterior. <strong>Manual:</strong> Valores inseridos
            manualmente pelo gestor.
          </p>
        </div>
      </div>
    </div>
  );
}
