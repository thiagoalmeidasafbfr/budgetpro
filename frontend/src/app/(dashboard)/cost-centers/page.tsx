"use client";

import { useState } from "react";
import {
  Building2,
  ChevronRight,
  ChevronDown,
  User,
  Search,
  Plus,
} from "lucide-react";
import { cn, formatCurrency, formatCompactCurrency } from "@/lib/utils";

interface CostCenterItem {
  id: string;
  code: string;
  name: string;
  department: string;
  responsible: string;
  budget: number;
  actual: number;
  forecast: number;
}

const MOCK_COST_CENTERS: CostCenterItem[] = [
  { id: "1", code: "CC001", name: "Tesouraria", department: "Financeiro", responsible: "Maria Silva", budget: 2880000, actual: 890000, forecast: 2750000 },
  { id: "2", code: "CC002", name: "Contabilidade", department: "Financeiro", responsible: "João Santos", budget: 1560000, actual: 420000, forecast: 1520000 },
  { id: "3", code: "CC003", name: "Vendas Nacionais", department: "Comercial", responsible: "Pedro Oliveira", budget: 3240000, actual: 980000, forecast: 3100000 },
  { id: "4", code: "CC004", name: "Vendas Internacionais", department: "Comercial", responsible: "Ana Costa", budget: 2160000, actual: 580000, forecast: 2050000 },
  { id: "5", code: "CC005", name: "Desenvolvimento", department: "Tecnologia", responsible: "Carlos Mendes", budget: 3600000, actual: 1120000, forecast: 3480000 },
  { id: "6", code: "CC006", name: "Infraestrutura TI", department: "Tecnologia", responsible: "Lucas Ferreira", budget: 1440000, actual: 420000, forecast: 1380000 },
  { id: "7", code: "CC007", name: "Recrutamento", department: "Recursos Humanos", responsible: "Fernanda Lima", budget: 960000, actual: 260000, forecast: 920000 },
  { id: "8", code: "CC008", name: "Treinamento", department: "Recursos Humanos", responsible: "Roberto Alves", budget: 720000, actual: 190000, forecast: 680000 },
];

const departments = [...new Set(MOCK_COST_CENTERS.map((cc) => cc.department))];

export default function CostCentersPage() {
  const [search, setSearch] = useState("");
  const [expandedDepts, setExpandedDepts] = useState<string[]>(departments);

  const toggleDept = (dept: string) => {
    setExpandedDepts((prev) =>
      prev.includes(dept) ? prev.filter((d) => d !== dept) : [...prev, dept]
    );
  };

  const filtered = MOCK_COST_CENTERS.filter(
    (cc) =>
      !search ||
      cc.name.toLowerCase().includes(search.toLowerCase()) ||
      cc.code.toLowerCase().includes(search.toLowerCase()) ||
      cc.responsible.toLowerCase().includes(search.toLowerCase())
  );

  const totalBudget = MOCK_COST_CENTERS.reduce((s, cc) => s + cc.budget, 0);
  const totalActual = MOCK_COST_CENTERS.reduce((s, cc) => s + cc.actual, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Centros de Custo
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Estrutura hierárquica: Empresa → Diretoria → Departamento → Centro
            de Custo
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
          <Plus className="w-4 h-4" />
          Novo Centro de Custo
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Total Centros de Custo
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {MOCK_COST_CENTERS.length}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Departamentos
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {departments.length}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Orçamento Total
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {formatCompactCurrency(totalBudget)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs text-muted-foreground font-medium uppercase">
            Realizado Total
          </p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {formatCompactCurrency(totalActual)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {((totalActual / totalBudget) * 100).toFixed(1)}% do orçamento
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar centro de custo, código ou responsável..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Hierarchical List */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        {departments.map((dept) => {
          const deptCCs = filtered.filter((cc) => cc.department === dept);
          if (deptCCs.length === 0 && search) return null;
          const isExpanded = expandedDepts.includes(dept);
          const deptBudget = deptCCs.reduce((s, cc) => s + cc.budget, 0);
          const deptActual = deptCCs.reduce((s, cc) => s + cc.actual, 0);
          const utilization =
            deptBudget > 0 ? (deptActual / deptBudget) * 100 : 0;

          return (
            <div key={dept}>
              {/* Department Header */}
              <button
                onClick={() => toggleDept(dept)}
                className="w-full flex items-center justify-between px-5 py-3.5 bg-muted/40 border-b border-border hover:bg-muted/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                  <Building2 className="w-4 h-4 text-primary" />
                  <span className="font-semibold text-sm text-foreground">
                    {dept}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({deptCCs.length} centros)
                  </span>
                </div>
                <div className="flex items-center gap-6 text-xs">
                  <div className="text-right">
                    <span className="text-muted-foreground">Orçado: </span>
                    <span className="font-semibold text-foreground">
                      {formatCompactCurrency(deptBudget)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-muted-foreground">Realizado: </span>
                    <span className="font-semibold text-foreground">
                      {formatCompactCurrency(deptActual)}
                    </span>
                  </div>
                  <div className="w-24">
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className={cn(
                          "h-1.5 rounded-full transition-all",
                          utilization > 80
                            ? "bg-red-500"
                            : utilization > 50
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                        )}
                        style={{ width: `${Math.min(utilization, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </button>

              {/* Cost Centers */}
              {isExpanded &&
                deptCCs.map((cc) => {
                  const ccUtil =
                    cc.budget > 0 ? (cc.actual / cc.budget) * 100 : 0;
                  const variance = cc.budget - cc.actual;

                  return (
                    <div
                      key={cc.id}
                      className="flex items-center justify-between px-5 py-3 pl-14 border-b border-border hover:bg-accent/50 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                          {cc.code}
                        </span>
                        <div>
                          <p className="font-medium text-sm text-foreground">
                            {cc.name}
                          </p>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <User className="w-3 h-3" />
                            {cc.responsible}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">
                            Orçado
                          </p>
                          <p className="text-sm font-medium text-foreground">
                            {formatCompactCurrency(cc.budget)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">
                            Realizado
                          </p>
                          <p className="text-sm font-medium text-foreground">
                            {formatCompactCurrency(cc.actual)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">
                            Forecast
                          </p>
                          <p className="text-sm font-medium text-foreground">
                            {formatCompactCurrency(cc.forecast)}
                          </p>
                        </div>
                        <div className="w-20">
                          <p className="text-xs text-muted-foreground text-right mb-0.5">
                            {ccUtil.toFixed(1)}%
                          </p>
                          <div className="w-full bg-muted rounded-full h-1.5">
                            <div
                              className={cn(
                                "h-1.5 rounded-full",
                                ccUtil > 80
                                  ? "bg-red-500"
                                  : ccUtil > 50
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              )}
                              style={{
                                width: `${Math.min(ccUtil, 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
