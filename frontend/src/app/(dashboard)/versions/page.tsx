"use client";

import { useState } from "react";
import {
  GitBranch,
  Plus,
  Lock,
  Check,
  Clock,
  FileEdit,
  Eye,
  ArrowLeftRight,
  MoreVertical,
} from "lucide-react";
import { cn, formatCurrency, formatCompactCurrency, getStatusColor } from "@/lib/utils";

interface BudgetVersion {
  id: string;
  name: string;
  year: number;
  status: "draft" | "under_review" | "approved" | "locked";
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  description: string;
  totalBudget: number;
  totalLines: number;
}

const MOCK_VERSIONS: BudgetVersion[] = [
  {
    id: "1",
    name: "Budget 2026 Original",
    year: 2026,
    status: "approved",
    createdBy: "Admin",
    createdAt: "2025-11-15",
    updatedAt: "2025-12-20",
    description: "Orçamento original aprovado para 2026",
    totalBudget: 15750000,
    totalLines: 160,
  },
  {
    id: "2",
    name: "Forecast Q1 2026",
    year: 2026,
    status: "draft",
    createdBy: "Financeiro",
    createdAt: "2026-03-01",
    updatedAt: "2026-03-10",
    description: "Forecast baseado no realizado do Q1",
    totalBudget: 14920000,
    totalLines: 160,
  },
  {
    id: "3",
    name: "Budget 2026 Revisado",
    year: 2026,
    status: "under_review",
    createdBy: "Financeiro",
    createdAt: "2026-02-15",
    updatedAt: "2026-03-05",
    description: "Revisão do orçamento após reestruturação comercial",
    totalBudget: 16100000,
    totalLines: 165,
  },
  {
    id: "4",
    name: "Budget 2025 Final",
    year: 2025,
    status: "locked",
    createdBy: "Admin",
    createdAt: "2024-11-10",
    updatedAt: "2025-12-31",
    description: "Orçamento 2025 fechado",
    totalBudget: 14200000,
    totalLines: 150,
  },
  {
    id: "5",
    name: "Budget 2025 Original",
    year: 2025,
    status: "locked",
    createdBy: "Admin",
    createdAt: "2024-11-01",
    updatedAt: "2025-01-15",
    description: "Orçamento original 2025",
    totalBudget: 13800000,
    totalLines: 148,
  },
];

const statusConfig: Record<
  string,
  { label: string; icon: React.ElementType; color: string }
> = {
  draft: {
    label: "Rascunho",
    icon: FileEdit,
    color: "bg-yellow-100 text-yellow-800",
  },
  under_review: {
    label: "Em Revisão",
    icon: Clock,
    color: "bg-blue-100 text-blue-800",
  },
  approved: {
    label: "Aprovado",
    icon: Check,
    color: "bg-green-100 text-green-800",
  },
  locked: {
    label: "Bloqueado",
    icon: Lock,
    color: "bg-gray-100 text-gray-800",
  },
};

export default function VersionsPage() {
  const [filterYear, setFilterYear] = useState("2026");
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  const filtered = MOCK_VERSIONS.filter(
    (v) => !filterYear || v.year.toString() === filterYear
  );

  const toggleCompare = (id: string) => {
    if (selectedForCompare.includes(id)) {
      setSelectedForCompare(selectedForCompare.filter((x) => x !== id));
    } else if (selectedForCompare.length < 2) {
      setSelectedForCompare([...selectedForCompare, id]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Controle de Versões
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie versões do orçamento e compare entre elas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setCompareMode(!compareMode);
              setSelectedForCompare([]);
            }}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
              compareMode
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:bg-accent"
            )}
          >
            <ArrowLeftRight className="w-4 h-4" />
            {compareMode ? "Cancelar Comparação" : "Comparar Versões"}
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Nova Versão
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={filterYear}
          onChange={(e) => setFilterYear(e.target.value)}
          className="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Todos os Anos</option>
          <option value="2026">2026</option>
          <option value="2025">2025</option>
        </select>
        {compareMode && (
          <span className="text-sm text-muted-foreground">
            Selecione 2 versões para comparar ({selectedForCompare.length}/2)
          </span>
        )}
        {compareMode && selectedForCompare.length === 2 && (
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
            <Eye className="w-4 h-4" />
            Ver Comparação
          </button>
        )}
      </div>

      {/* Versions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((version) => {
          const statusInfo = statusConfig[version.status];
          const StatusIcon = statusInfo.icon;
          const isSelected = selectedForCompare.includes(version.id);

          return (
            <div
              key={version.id}
              onClick={() => compareMode && toggleCompare(version.id)}
              className={cn(
                "rounded-xl border bg-card p-5 shadow-sm transition-all",
                compareMode && "cursor-pointer hover:shadow-md",
                isSelected
                  ? "border-primary ring-2 ring-primary/20"
                  : "border-border"
              )}
            >
              {/* Version Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                    <GitBranch className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground text-sm">
                      {version.name}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {version.year}
                    </p>
                  </div>
                </div>
                <span
                  className={cn(
                    "flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium",
                    statusInfo.color
                  )}
                >
                  <StatusIcon className="w-3 h-3" />
                  {statusInfo.label}
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-muted-foreground mb-4 line-clamp-2">
                {version.description}
              </p>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-2.5 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">
                    Total Orçado
                  </p>
                  <p className="text-sm font-bold text-foreground">
                    {formatCompactCurrency(version.totalBudget)}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">
                    Linhas
                  </p>
                  <p className="text-sm font-bold text-foreground">
                    {version.totalLines}
                  </p>
                </div>
              </div>

              {/* Meta */}
              <div className="flex items-center justify-between text-xs text-muted-foreground border-t border-border pt-3">
                <span>Por: {version.createdBy}</span>
                <span>
                  Atualizado:{" "}
                  {new Date(version.updatedAt).toLocaleDateString("pt-BR")}
                </span>
              </div>

              {/* Actions */}
              {!compareMode && (
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
                  <button className="flex-1 text-xs py-1.5 rounded-md border border-border hover:bg-accent transition-colors font-medium">
                    Visualizar
                  </button>
                  {version.status === "draft" && (
                    <button className="flex-1 text-xs py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-medium">
                      Editar
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
