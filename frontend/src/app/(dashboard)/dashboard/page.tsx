"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
} from "recharts";
import { DollarSign, TrendingUp, Target, AlertTriangle } from "lucide-react";
import { formatCurrency, formatCompactCurrency, cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MONTHS = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

const monthlyBudget = [
  1_200_000, 1_300_000, 1_350_000, 1_250_000, 1_400_000, 1_350_000,
  1_300_000, 1_350_000, 1_250_000, 1_300_000, 1_400_000, 1_500_000,
];

const monthlyActual = [
  1_150_000, 1_280_000, 1_420_000, 0, 0, 0,
  0, 0, 0, 0, 0, 0,
];

const orcadoVsRealizadoData = MONTHS.map((month, i) => ({
  month,
  orcado: monthlyBudget[i],
  realizado: monthlyActual[i] || null,
}));

const acumuladoData = (() => {
  let accBudget = 0;
  let accActual = 0;
  return MONTHS.map((month, i) => {
    accBudget += monthlyBudget[i];
    accActual += monthlyActual[i];
    return {
      month,
      orcadoAcum: accBudget,
      realizadoAcum: monthlyActual[i] > 0 ? accActual : null,
    };
  });
})();

const burnRateData = (() => {
  const spent = monthlyActual.filter((v) => v > 0);
  const avg = spent.reduce((a, b) => a + b, 0) / (spent.length || 1);
  return MONTHS.map((month, i) => ({
    month,
    gasto: monthlyActual[i] || null,
    media: monthlyActual[i] > 0 ? avg : null,
  }));
})();

const topCentrosDeCusto = [
  { nome: "Desenvolvimento", valor: 890_000 },
  { nome: "Vendas Nacionais", valor: 780_000 },
  { nome: "Tesouraria", valor: 650_000 },
  { nome: "Infraestrutura TI", valor: 520_000 },
  { nome: "Vendas Internacionais", valor: 480_000 },
  { nome: "Contabilidade", valor: 350_000 },
  { nome: "Treinamento", valor: 320_000 },
  { nome: "Recrutamento", valor: 290_000 },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const COLORS = {
  orcado: "#3b82f6",
  realizado: "#10b981",
  forecast: "#8b5cf6",
  warning: "#f59e0b",
} as const;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function tooltipFormatter(value: any) {
  return formatCompactCurrency(value);
}

function brlTickFormatter(value: number) {
  return formatCompactCurrency(value);
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  iconBgClass: string;
  trend?: string;
  trendPositive?: boolean;
}

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconBgClass,
  trend,
  trendPositive,
}: KpiCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        <div
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-lg",
            iconBgClass,
          )}
        >
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
      {trend && (
        <p
          className={cn(
            "mt-3 text-xs font-medium",
            trendPositive ? "text-emerald-600" : "text-red-600",
          )}
        >
          {trend}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart wrapper
// ---------------------------------------------------------------------------

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [selectedYear, setSelectedYear] = useState<number>(2025);

  return (
    <div className="space-y-6 p-6">
      {/* ---- Header ---- */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Dashboard Financeiro
          </h1>
          <p className="text-sm text-muted-foreground">
            Visão consolidada do orçamento corporativo
          </p>
        </div>

        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value={2024}>2024</option>
          <option value={2025}>2025</option>
          <option value={2026}>2026</option>
        </select>
      </div>

      {/* ---- KPI Cards ---- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Orçamento Total"
          value={formatCurrency(15_750_000)}
          icon={DollarSign}
          iconBgClass="bg-blue-500"
          trend="+2.1% vs ano anterior"
          trendPositive
        />
        <KpiCard
          title="Realizado"
          value={formatCurrency(4_280_350)}
          subtitle="27.2% do orçamento"
          icon={TrendingUp}
          iconBgClass="bg-emerald-500"
          trend="3 de 12 meses"
          trendPositive
        />
        <KpiCard
          title="Forecast"
          value={formatCurrency(14_920_000)}
          subtitle="94.7% do orçamento"
          icon={Target}
          iconBgClass="bg-violet-500"
          trend="-5.3% abaixo do orçado"
          trendPositive
        />
        <KpiCard
          title="Desvio"
          value={formatCurrency(830_000)}
          subtitle="5.3% do orçamento"
          icon={AlertTriangle}
          iconBgClass="bg-amber-500"
          trend="Dentro da margem aceitável"
          trendPositive
        />
      </div>

      {/* ---- Charts Row 1 ---- */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Orçado vs Realizado */}
        <ChartCard title="Orçado vs Realizado">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={orcadoVsRealizadoData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={tooltipFormatter}
                labelStyle={{ fontWeight: 600 }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}
              />
              <Legend />
              <Bar
                dataKey="orcado"
                name="Orçado"
                fill={COLORS.orcado}
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="realizado"
                name="Realizado"
                fill={COLORS.realizado}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Realizado Acumulado */}
        <ChartCard title="Realizado Acumulado">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={acumuladoData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={tooltipFormatter}
                labelStyle={{ fontWeight: 600 }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="orcadoAcum"
                name="Orçado Acumulado"
                stroke={COLORS.orcado}
                fill={COLORS.orcado}
                fillOpacity={0.15}
              />
              <Area
                type="monotone"
                dataKey="realizadoAcum"
                name="Realizado Acumulado"
                stroke={COLORS.realizado}
                fill={COLORS.realizado}
                fillOpacity={0.25}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* ---- Charts Row 2 ---- */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Burn Rate */}
        <ChartCard title="Burn Rate Mensal">
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={burnRateData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={brlTickFormatter} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={tooltipFormatter}
                labelStyle={{ fontWeight: 600 }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}
              />
              <Legend />
              <Bar
                dataKey="gasto"
                name="Gasto Mensal"
                fill={COLORS.warning}
                radius={[4, 4, 0, 0]}
              />
              <Line
                type="monotone"
                dataKey="media"
                name="Média"
                stroke={COLORS.forecast}
                strokeWidth={2}
                dot={false}
                strokeDasharray="6 3"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top Centros de Custo */}
        <ChartCard title="Top Centros de Custo">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={topCentrosDeCusto}
              layout="vertical"
              margin={{ left: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                type="number"
                tickFormatter={brlTickFormatter}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                type="category"
                dataKey="nome"
                tick={{ fontSize: 12 }}
                width={130}
              />
              <Tooltip
                formatter={tooltipFormatter}
                labelStyle={{ fontWeight: 600 }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}
              />
              <Bar
                dataKey="valor"
                name="Valor"
                fill={COLORS.orcado}
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
