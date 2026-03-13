"use client";

import { useState, useMemo, useCallback, Fragment } from "react";
import { Upload, Download, Plus, Search, MessageSquare, Filter } from "lucide-react";
import { formatCurrency, cn, MONTHS, MONTH_KEYS } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Categoria = "Receita" | "Custo" | "Despesa" | "Investimento";

interface BudgetRow {
  id: string;
  centroCusto: string;
  centroCustoCode: string;
  contaContabil: string;
  categoria: Categoria;
  valores: number[]; // 12 months
}

// ---------------------------------------------------------------------------
// Mock Data
// ---------------------------------------------------------------------------

const MOCK_DATA: BudgetRow[] = [
  // CC001 Tesouraria
  {
    id: "1",
    centroCusto: "CC001 Tesouraria",
    centroCustoCode: "CC001",
    contaContabil: "3.1.01 Receita de Vendas Nacionais",
    categoria: "Receita",
    valores: [850000, 920000, 880000, 950000, 1100000, 1050000, 980000, 1020000, 1080000, 1150000, 1200000, 1350000],
  },
  {
    id: "2",
    centroCusto: "CC001 Tesouraria",
    centroCustoCode: "CC001",
    contaContabil: "3.1.02 Receita de Vendas Internacionais",
    categoria: "Receita",
    valores: [320000, 350000, 310000, 380000, 420000, 400000, 370000, 390000, 410000, 440000, 460000, 500000],
  },
  {
    id: "3",
    centroCusto: "CC001 Tesouraria",
    centroCustoCode: "CC001",
    contaContabil: "5.1.01 Salários e Encargos",
    categoria: "Despesa",
    valores: [120000, 120000, 122000, 122000, 122000, 125000, 125000, 125000, 128000, 128000, 128000, 130000],
  },
  {
    id: "4",
    centroCusto: "CC001 Tesouraria",
    centroCustoCode: "CC001",
    contaContabil: "5.1.03 Aluguel",
    categoria: "Despesa",
    valores: [18000, 18000, 18000, 18000, 18000, 18000, 18000, 18000, 18000, 18000, 18000, 18000],
  },
  {
    id: "5",
    centroCusto: "CC001 Tesouraria",
    centroCustoCode: "CC001",
    contaContabil: "4.1.01 Custo de Mercadorias Vendidas",
    categoria: "Custo",
    valores: [510000, 552000, 528000, 570000, 660000, 630000, 588000, 612000, 648000, 690000, 720000, 810000],
  },
  // CC003 Vendas Nacionais
  {
    id: "6",
    centroCusto: "CC003 Vendas Nacionais",
    centroCustoCode: "CC003",
    contaContabil: "5.1.01 Salários e Encargos",
    categoria: "Despesa",
    valores: [95000, 95000, 97000, 97000, 97000, 99000, 99000, 99000, 101000, 101000, 101000, 103000],
  },
  {
    id: "7",
    centroCusto: "CC003 Vendas Nacionais",
    centroCustoCode: "CC003",
    contaContabil: "5.1.06 Viagens e Hospedagem",
    categoria: "Despesa",
    valores: [35000, 28000, 42000, 30000, 38000, 45000, 32000, 36000, 40000, 33000, 37000, 48000],
  },
  {
    id: "8",
    centroCusto: "CC003 Vendas Nacionais",
    centroCustoCode: "CC003",
    contaContabil: "5.1.07 Marketing",
    categoria: "Despesa",
    valores: [65000, 55000, 60000, 70000, 58000, 75000, 62000, 68000, 72000, 60000, 65000, 80000],
  },
  {
    id: "9",
    centroCusto: "CC003 Vendas Nacionais",
    centroCustoCode: "CC003",
    contaContabil: "5.1.08 Comissões de Vendas",
    categoria: "Despesa",
    valores: [42500, 46000, 44000, 47500, 55000, 52500, 49000, 51000, 54000, 57500, 60000, 67500],
  },
  // CC005 Desenvolvimento
  {
    id: "10",
    centroCusto: "CC005 Desenvolvimento",
    centroCustoCode: "CC005",
    contaContabil: "5.1.01 Salários e Encargos",
    categoria: "Despesa",
    valores: [180000, 180000, 185000, 185000, 185000, 190000, 190000, 190000, 195000, 195000, 195000, 200000],
  },
  {
    id: "11",
    centroCusto: "CC005 Desenvolvimento",
    centroCustoCode: "CC005",
    contaContabil: "6.1.01 Licenças de Software",
    categoria: "Investimento",
    valores: [45000, 45000, 45000, 45000, 45000, 48000, 48000, 48000, 48000, 48000, 48000, 48000],
  },
  {
    id: "12",
    centroCusto: "CC005 Desenvolvimento",
    centroCustoCode: "CC005",
    contaContabil: "6.1.02 Equipamentos de TI",
    categoria: "Investimento",
    valores: [25000, 15000, 35000, 20000, 15000, 50000, 10000, 20000, 15000, 25000, 30000, 40000],
  },
  {
    id: "13",
    centroCusto: "CC005 Desenvolvimento",
    centroCustoCode: "CC005",
    contaContabil: "5.1.09 Treinamento e Capacitação",
    categoria: "Despesa",
    valores: [12000, 8000, 15000, 10000, 12000, 18000, 8000, 10000, 14000, 12000, 16000, 20000],
  },
  // CC007 Administrativo
  {
    id: "14",
    centroCusto: "CC007 Administrativo",
    centroCustoCode: "CC007",
    contaContabil: "5.1.01 Salários e Encargos",
    categoria: "Despesa",
    valores: [85000, 85000, 87000, 87000, 87000, 89000, 89000, 89000, 91000, 91000, 91000, 93000],
  },
  {
    id: "15",
    centroCusto: "CC007 Administrativo",
    centroCustoCode: "CC007",
    contaContabil: "5.1.04 Serviços de Terceiros",
    categoria: "Despesa",
    valores: [22000, 24000, 21000, 23000, 25000, 22000, 24000, 21000, 23000, 25000, 22000, 26000],
  },
  {
    id: "16",
    centroCusto: "CC007 Administrativo",
    centroCustoCode: "CC007",
    contaContabil: "5.1.05 Material de Escritório",
    categoria: "Despesa",
    valores: [4500, 3800, 5200, 4000, 4300, 3900, 4600, 4100, 4800, 3700, 4200, 5500],
  },
  {
    id: "17",
    centroCusto: "CC007 Administrativo",
    centroCustoCode: "CC007",
    contaContabil: "5.1.03 Aluguel",
    categoria: "Despesa",
    valores: [32000, 32000, 32000, 32000, 32000, 32000, 32000, 32000, 32000, 32000, 32000, 32000],
  },
  // CC009 Operações
  {
    id: "18",
    centroCusto: "CC009 Operações",
    centroCustoCode: "CC009",
    contaContabil: "4.1.02 Custo de Serviços Prestados",
    categoria: "Custo",
    valores: [145000, 152000, 148000, 155000, 162000, 158000, 150000, 156000, 160000, 165000, 170000, 178000],
  },
  {
    id: "19",
    centroCusto: "CC009 Operações",
    centroCustoCode: "CC009",
    contaContabil: "5.1.01 Salários e Encargos",
    categoria: "Despesa",
    valores: [110000, 110000, 112000, 112000, 112000, 115000, 115000, 115000, 118000, 118000, 118000, 120000],
  },
  {
    id: "20",
    centroCusto: "CC009 Operações",
    centroCustoCode: "CC009",
    contaContabil: "6.1.03 Veículos e Equipamentos",
    categoria: "Investimento",
    valores: [60000, 0, 0, 80000, 0, 0, 45000, 0, 0, 70000, 0, 0],
  },
];

const CENTROS_CUSTO = [
  "Todos",
  "CC001 Tesouraria",
  "CC003 Vendas Nacionais",
  "CC005 Desenvolvimento",
  "CC007 Administrativo",
  "CC009 Operações",
];

const CATEGORIAS: ("Todas" | Categoria)[] = [
  "Todas",
  "Receita",
  "Custo",
  "Despesa",
  "Investimento",
];

const CATEGORIA_COLORS: Record<Categoria, string> = {
  Receita: "bg-green-100 text-green-800",
  Custo: "bg-red-100 text-red-800",
  Despesa: "bg-orange-100 text-orange-800",
  Investimento: "bg-purple-100 text-purple-800",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function rowTotal(valores: number[]): number {
  return valores.reduce((sum, v) => sum + v, 0);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BudgetPage() {
  const [data, setData] = useState<BudgetRow[]>(MOCK_DATA);
  const [selectedCell, setSelectedCell] = useState<{ rowId: string; monthIdx: number } | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [filterCC, setFilterCC] = useState("Todos");
  const [filterCategoria, setFilterCategoria] = useState<"Todas" | Categoria>("Todas");
  const [searchText, setSearchText] = useState("");
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  // Filtered data
  const filteredData = useMemo(() => {
    return data.filter((row) => {
      if (filterCC !== "Todos" && row.centroCusto !== filterCC) return false;
      if (filterCategoria !== "Todas" && row.categoria !== filterCategoria) return false;
      if (
        searchText &&
        !row.contaContabil.toLowerCase().includes(searchText.toLowerCase()) &&
        !row.centroCusto.toLowerCase().includes(searchText.toLowerCase())
      )
        return false;
      return true;
    });
  }, [data, filterCC, filterCategoria, searchText]);

  // Group by centro de custo
  const grouped = useMemo(() => {
    const map = new Map<string, BudgetRow[]>();
    for (const row of filteredData) {
      const existing = map.get(row.centroCusto) || [];
      existing.push(row);
      map.set(row.centroCusto, existing);
    }
    return map;
  }, [filteredData]);

  // Grand totals
  const grandTotals = useMemo(() => {
    const totals = new Array(12).fill(0);
    for (const row of filteredData) {
      for (let i = 0; i < 12; i++) {
        totals[i] += row.valores[i];
      }
    }
    return totals;
  }, [filteredData]);

  // Subtotals per CC
  const subtotals = useMemo(() => {
    const map = new Map<string, number[]>();
    for (const [cc, rows] of grouped) {
      const totals = new Array(12).fill(0);
      for (const row of rows) {
        for (let i = 0; i < 12; i++) {
          totals[i] += row.valores[i];
        }
      }
      map.set(cc, totals);
    }
    return map;
  }, [grouped]);

  const handleCellClick = useCallback(
    (rowId: string, monthIdx: number) => {
      const row = data.find((r) => r.id === rowId);
      if (!row) return;
      setSelectedCell({ rowId, monthIdx });
      setEditValue(String(row.valores[monthIdx]));
    },
    [data]
  );

  const commitEdit = useCallback(() => {
    if (!selectedCell) return;
    const numVal = parseFloat(editValue) || 0;
    setData((prev) =>
      prev.map((row) => {
        if (row.id !== selectedCell.rowId) return row;
        const newValores = [...row.valores];
        newValores[selectedCell.monthIdx] = numVal;
        return { ...row, valores: newValores };
      })
    );
    setSelectedCell(null);
    setEditValue("");
  }, [selectedCell, editValue]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        commitEdit();
      } else if (e.key === "Escape") {
        setSelectedCell(null);
        setEditValue("");
      }
    },
    [commitEdit]
  );

  // Sticky column widths
  const stickyCol1 = "left-0 w-[180px] min-w-[180px]";
  const stickyCol2 = "left-[180px] w-[240px] min-w-[240px]";
  const stickyCol3 = "left-[420px] w-[120px] min-w-[120px]";

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* ---------------------------------------------------------------- */}
      {/* Header                                                           */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight">Planejamento Orçamentário</h1>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Version selector */}
          <select
            className="h-9 rounded-md border border-input bg-card px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary"
            defaultValue="budget-2026-original"
          >
            <option value="budget-2026-original">Budget 2026 Original</option>
            <option value="budget-2026-rev1">Budget 2026 Rev.1</option>
            <option value="forecast-2026-q1">Forecast 2026 Q1</option>
          </select>

          {/* Status badge */}
          <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-800">
            Aprovado
          </span>

          <div className="flex-1" />

          {/* Action buttons */}
          <button className="inline-flex items-center gap-2 rounded-md border border-input bg-card px-3 py-2 text-sm font-medium shadow-sm hover:bg-muted transition-colors">
            <Upload className="h-4 w-4" />
            Importar Excel
          </button>
          <button className="inline-flex items-center gap-2 rounded-md border border-input bg-card px-3 py-2 text-sm font-medium shadow-sm hover:bg-muted transition-colors">
            <Download className="h-4 w-4" />
            Exportar Excel
          </button>
          <button className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors">
            <Plus className="h-4 w-4" />
            Adicionar Linha
          </button>
        </div>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* Filter Bar                                                       */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex items-center gap-3 flex-wrap rounded-lg border border-border bg-card p-3">
        <Filter className="h-4 w-4 text-muted-foreground" />

        <select
          value={filterCC}
          onChange={(e) => setFilterCC(e.target.value)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {CENTROS_CUSTO.map((cc) => (
            <option key={cc} value={cc}>
              {cc === "Todos" ? "Centro de Custo" : cc}
            </option>
          ))}
        </select>

        <select
          value={filterCategoria}
          onChange={(e) => setFilterCategoria(e.target.value as "Todas" | Categoria)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {CATEGORIAS.map((cat) => (
            <option key={cat} value={cat}>
              {cat === "Todas" ? "Categoria" : cat}
            </option>
          ))}
        </select>

        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar conta ou centro..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="h-8 w-64 rounded-md border border-input bg-background pl-8 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* Spreadsheet Table                                                */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex-1 overflow-auto rounded-lg border border-border bg-card shadow-sm">
        <table className="w-full border-collapse text-sm">
          {/* Table Head */}
          <thead className="sticky top-0 z-20">
            <tr className="bg-muted">
              <th
                className={cn(
                  "sticky z-30 bg-muted px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground border-b border-r border-border",
                  stickyCol1
                )}
              >
                Centro de Custo
              </th>
              <th
                className={cn(
                  "sticky z-30 bg-muted px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground border-b border-r border-border",
                  stickyCol2
                )}
              >
                Conta Contábil
              </th>
              <th
                className={cn(
                  "sticky z-30 bg-muted px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground border-b border-r border-border",
                  stickyCol3
                )}
              >
                Categoria
              </th>
              {MONTHS.map((m) => (
                <th
                  key={m}
                  className="bg-muted px-3 py-2 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground border-b border-r border-border whitespace-nowrap min-w-[110px]"
                >
                  {m}
                </th>
              ))}
              <th className="bg-muted px-3 py-2 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground border-b border-border whitespace-nowrap min-w-[130px]">
                Total
              </th>
              {/* Comment column */}
              <th className="bg-muted px-2 py-2 border-b border-border w-10 min-w-[40px]" />
            </tr>
          </thead>

          <tbody>
            {Array.from(grouped.entries()).map(([cc, rows]) => {
              const ccSubtotals = subtotals.get(cc) || new Array(12).fill(0);

              return (
                <Fragment key={cc}>
                  {/* Data rows */}
                  {rows.map((row, rowIdx) => {
                    const total = rowTotal(row.valores);
                    const isHovered = hoveredRow === row.id;

                    return (
                      <tr
                        key={row.id}
                        className={cn(
                          "transition-colors border-b border-border",
                          rowIdx % 2 === 0 ? "bg-card" : "bg-muted/20",
                          isHovered && "bg-accent/50"
                        )}
                        onMouseEnter={() => setHoveredRow(row.id)}
                        onMouseLeave={() => setHoveredRow(null)}
                      >
                        {/* Centro de Custo */}
                        <td
                          className={cn(
                            "sticky z-10 px-3 py-2 text-left font-medium text-foreground border-r border-border truncate",
                            stickyCol1,
                            rowIdx % 2 === 0 ? "bg-card" : "bg-muted/20",
                            isHovered && "bg-accent/50"
                          )}
                        >
                          {row.centroCusto}
                        </td>

                        {/* Conta Contábil */}
                        <td
                          className={cn(
                            "sticky z-10 px-3 py-2 text-left text-foreground border-r border-border truncate",
                            stickyCol2,
                            rowIdx % 2 === 0 ? "bg-card" : "bg-muted/20",
                            isHovered && "bg-accent/50"
                          )}
                        >
                          {row.contaContabil}
                        </td>

                        {/* Categoria */}
                        <td
                          className={cn(
                            "sticky z-10 px-3 py-2 text-left border-r border-border",
                            stickyCol3,
                            rowIdx % 2 === 0 ? "bg-card" : "bg-muted/20",
                            isHovered && "bg-accent/50"
                          )}
                        >
                          <span
                            className={cn(
                              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
                              CATEGORIA_COLORS[row.categoria]
                            )}
                          >
                            {row.categoria}
                          </span>
                        </td>

                        {/* Monthly values */}
                        {row.valores.map((val, mIdx) => {
                          const isSelected =
                            selectedCell?.rowId === row.id && selectedCell?.monthIdx === mIdx;

                          return (
                            <td
                              key={mIdx}
                              className={cn(
                                "px-3 py-2 text-right border-r border-border whitespace-nowrap cursor-pointer",
                                isSelected && "ring-2 ring-primary ring-inset rounded-sm"
                              )}
                              onClick={() => handleCellClick(row.id, mIdx)}
                            >
                              {isSelected ? (
                                <input
                                  type="number"
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  onBlur={commitEdit}
                                  onKeyDown={handleKeyDown}
                                  autoFocus
                                  className="w-full bg-transparent text-right text-sm outline-none"
                                />
                              ) : (
                                <span className="text-sm tabular-nums">
                                  {formatCurrency(val)}
                                </span>
                              )}
                            </td>
                          );
                        })}

                        {/* Total */}
                        <td className="px-3 py-2 text-right font-semibold bg-muted/30 whitespace-nowrap border-r border-border">
                          <span className="text-sm tabular-nums">{formatCurrency(total)}</span>
                        </td>

                        {/* Comment icon */}
                        <td className="px-2 py-2 text-center">
                          <MessageSquare
                            className={cn(
                              "h-4 w-4 text-muted-foreground/40 transition-opacity mx-auto",
                              isHovered ? "opacity-100" : "opacity-0"
                            )}
                          />
                        </td>
                      </tr>
                    );
                  })}

                  {/* Subtotal row */}
                  <tr className="border-b-2 border-border bg-muted/40">
                    <td
                      className={cn(
                        "sticky z-10 bg-muted/40 px-3 py-2 text-left font-semibold text-foreground border-r border-border",
                        stickyCol1
                      )}
                    >
                      Subtotal {cc.split(" ").slice(1).join(" ")}
                    </td>
                    <td
                      className={cn(
                        "sticky z-10 bg-muted/40 px-3 py-2 border-r border-border",
                        stickyCol2
                      )}
                    />
                    <td
                      className={cn(
                        "sticky z-10 bg-muted/40 px-3 py-2 border-r border-border",
                        stickyCol3
                      )}
                    />
                    {ccSubtotals.map((val: number, mIdx: number) => (
                      <td
                        key={mIdx}
                        className="px-3 py-2 text-right font-semibold border-r border-border whitespace-nowrap"
                      >
                        <span className="text-sm tabular-nums">{formatCurrency(val)}</span>
                      </td>
                    ))}
                    <td className="px-3 py-2 text-right font-bold bg-muted/50 whitespace-nowrap border-r border-border">
                      <span className="text-sm tabular-nums">
                        {formatCurrency(rowTotal(ccSubtotals))}
                      </span>
                    </td>
                    <td className="px-2 py-2" />
                  </tr>
                </Fragment>
              );
            })}
          </tbody>

          {/* Grand Total Footer */}
          <tfoot className="sticky bottom-0 z-20">
            <tr className="bg-muted border-t-2 border-primary">
              <td
                className={cn(
                  "sticky z-30 bg-muted px-3 py-3 text-left font-bold text-foreground border-r border-border text-sm",
                  stickyCol1
                )}
              >
                Total Geral
              </td>
              <td
                className={cn(
                  "sticky z-30 bg-muted px-3 py-3 border-r border-border",
                  stickyCol2
                )}
              />
              <td
                className={cn(
                  "sticky z-30 bg-muted px-3 py-3 border-r border-border",
                  stickyCol3
                )}
              />
              {grandTotals.map((val: number, mIdx: number) => (
                <td
                  key={mIdx}
                  className="bg-muted px-3 py-3 text-right font-bold border-r border-border whitespace-nowrap"
                >
                  <span className="text-sm tabular-nums">{formatCurrency(val)}</span>
                </td>
              ))}
              <td className="bg-primary/10 px-3 py-3 text-right font-bold whitespace-nowrap border-r border-border">
                <span className="text-sm tabular-nums text-primary">
                  {formatCurrency(rowTotal(grandTotals))}
                </span>
              </td>
              <td className="bg-muted px-2 py-3" />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

