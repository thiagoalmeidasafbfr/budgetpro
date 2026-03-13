"use client";

import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  AreaChart, Area, ComposedChart, Line, ResponsiveContainer,
} from "recharts";
import { DollarSign, TrendingUp, Target, AlertTriangle, RefreshCw } from "lucide-react";
import { formatCurrency, formatCompactCurrency, cn } from "@/lib/utils";
import {
  dashboardApi,
  type DashboardKPIs, type MonthlyData, type CumulativeData,
  type BurnRateData, type TopItem,
} from "@/lib/api";

const COLORS = {
  orcado: "#3b82f6", realizado: "#10b981",
  forecast: "#8b5cf6", warning: "#f59e0b",
} as const;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function tooltipFormatter(value: any) { return formatCompactCurrency(value); }
function brlTickFormatter(value: number) { return formatCompactCurrency(value); }

function KpiCard({ title, value, subtitle, icon: Icon, iconBgClass, trend, trendPositive, loading }: {
  title: string; value: string; subtitle?: string;
  icon: React.ElementType; iconBgClass: string;
  trend?: string; trendPositive?: boolean; loading?: boolean;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {loading
            ? <div className="h-8 w-32 animate-pulse rounded bg-muted" />
            : <p className="text-2xl font-bold tracking-tight">{value}</p>}
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        </div>
        <div className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-lg", iconBgClass)}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
      {trend && !loading && (
        <p className={cn("mt-3 text-xs font-medium", trendPositive ? "text-emerald-600" : "text-red-600")}>{trend}</p>
      )}
    </div>
  );
}

function ChartCard({ title, children, loading }: { title: string; children: React.ReactNode; loading?: boolean }) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      {loading ? <div className="h-80 w-full animate-pulse rounded bg-muted" /> : children}
    </div>
  );
}

export default function DashboardPage() {
  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [budgetVsActual, setBudgetVsActual] = useState<MonthlyData[]>([]);
  const [cumulative, setCumulative] = useState<CumulativeData[]>([]);
  const [burnRate, setBurnRate] = useState<BurnRateData[]>([]);
  const [topCostCenters, setTopCostCenters] = useState<TopItem[]>([]);

  const fetchAll = async (year: number) => {
    setLoading(true);
    setError(null);
    try {
      const [kpisData, bvaData, cumData, brData, topCCData] = await Promise.all([
        dashboardApi.getKpis(year),
        dashboardApi.getBudgetVsActual(year),
        dashboardApi.getCumulative(year),
        dashboardApi.getBurnRate(year),
        dashboardApi.getTopCostCenters(year, 8),
      ]);
      setKpis(kpisData);
      setBudgetVsActual(bvaData);
      setCumulative(cumData);
      setBurnRate(brData);
      setTopCostCenters(topCCData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados do dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(selectedYear); }, [selectedYear]);

  const utilizacao = kpis?.budget_utilization_pct ?? 0;
  const variancePct = kpis?.variance_pct ?? 0;

  const orcadoVsRealizadoData = budgetVsActual.map((d) => ({
    month: d.month, orcado: d.budget, realizado: d.actual > 0 ? d.actual : null,
  }));
  const acumuladoData = cumulative.map((d) => ({
    month: d.month, orcadoAcum: d.cumulative_budget,
    realizadoAcum: d.cumulative_actual > 0 ? d.cumulative_actual : null,
  }));
  const burnRateData = burnRate.map((d) => ({
    month: d.month,
    gasto: d.monthly_spend > 0 ? d.monthly_spend : null,
    media: d.avg_monthly_spend > 0 ? d.avg_monthly_spend : null,
  }));
  const topCCData = topCostCenters.map((d) => ({ nome: d.name, valor: d.amount }));

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard Financeiro</h1>
          <p className="text-sm text-muted-foreground">Visão consolidada do orçamento corporativo</p>
        </div>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {[2024, 2025, 2026].map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <span>{error}</span>
          <button onClick={() => fetchAll(selectedYear)} className="ml-4 flex items-center gap-1 font-medium hover:underline">
            <RefreshCw className="h-3.5 w-3.5" /> Tentar novamente
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Orçamento Total" value={formatCurrency(kpis?.total_budget ?? 0)}
          icon={DollarSign} iconBgClass="bg-blue-500" trend={`Ano ${selectedYear}`} trendPositive loading={loading} />
        <KpiCard title="Realizado" value={formatCurrency(kpis?.total_actual ?? 0)}
          subtitle={kpis ? `${utilizacao.toFixed(1)}% do orçamento` : undefined}
          icon={TrendingUp} iconBgClass="bg-emerald-500"
          trend={kpis ? `Utilização: ${utilizacao.toFixed(1)}%` : undefined}
          trendPositive={utilizacao <= 100} loading={loading} />
        <KpiCard title="Forecast" value={formatCurrency(kpis?.total_forecast ?? 0)}
          icon={Target} iconBgClass="bg-violet-500" loading={loading} />
        <KpiCard title="Desvio (Budget - Real)" value={formatCurrency(Math.abs(kpis?.variance ?? 0))}
          subtitle={kpis ? `${Math.abs(variancePct).toFixed(1)}% do orçamento` : undefined}
          icon={AlertTriangle} iconBgClass={(kpis?.variance ?? 0) >= 0 ? "bg-emerald-500" : "bg-red-500"}
          trend={kpis ? ((kpis.variance ?? 0) >= 0 ? "Dentro do orçamento" : "Acima do orçamento") : undefined}
          trendPositive={(kpis?.variance ?? 0) >= 0} loading={loading} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Orçado vs Realizado" loading={loading}>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={orcadoVsRealizadoData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip formatter={tooltipFormatter} labelStyle={{ fontWeight: 600 }} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
              <Legend />
              <Bar dataKey="orcado" name="Orçado" fill={COLORS.orcado} radius={[4, 4, 0, 0]} />
              <Bar dataKey="realizado" name="Realizado" fill={COLORS.realizado} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Realizado Acumulado" loading={loading}>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={acumuladoData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip formatter={tooltipFormatter} labelStyle={{ fontWeight: 600 }} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
              <Legend />
              <Area type="monotone" dataKey="orcadoAcum" name="Orçado Acumulado" stroke={COLORS.orcado} fill={COLORS.orcado} fillOpacity={0.15} />
              <Area type="monotone" dataKey="realizadoAcum" name="Realizado Acumulado" stroke={COLORS.realizado} fill={COLORS.realizado} fillOpacity={0.25} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Burn Rate Mensal" loading={loading}>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={burnRateData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip formatter={tooltipFormatter} labelStyle={{ fontWeight: 600 }} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
              <Legend />
              <Bar dataKey="gasto" name="Gasto Mensal" fill={COLORS.warning} radius={[4, 4, 0, 0]} />
              <Line type="monotone" dataKey="media" name="Média" stroke={COLORS.forecast} strokeWidth={2} dot={false} strokeDasharray="6 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top Centros de Custo" loading={loading}>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={topCCData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis type="number" tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="nome" tick={{ fontSize: 12 }} width={130} />
              <Tooltip formatter={tooltipFormatter} labelStyle={{ fontWeight: 600 }} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
              <Bar dataKey="valor" name="Valor" fill={COLORS.orcado} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
