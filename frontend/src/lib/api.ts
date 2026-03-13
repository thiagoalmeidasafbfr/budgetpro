const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("auth_token");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
    const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
          window.location.href = "/login";
        }
      }
      const error = await response.json().catch(() => ({ message: "Erro na requisição" }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    if (response.status === 204) return {} as T;
    return response.json();
  }

  async get<T>(endpoint: string, params?: Record<string, string | number | undefined>): Promise<T> {
    let url = endpoint;
    if (params) {
      const filtered = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null).map(([k, v]) => [k, String(v)])
      );
      const qs = new URLSearchParams(filtered).toString();
      if (qs) url = `${endpoint}?${qs}`;
    }
    return this.request<T>(url, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "POST", body: data ? JSON.stringify(data) : undefined });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "PUT", body: data ? JSON.stringify(data) : undefined });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
    const response = await fetch(`${this.baseUrl}${endpoint}`, { method: "POST", headers, body: formData });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: "Erro no upload" }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    return response.json();
  }
}

export const api = new ApiClient(BASE_URL);
export default api;

// ---- Types ----

export interface DashboardKPIs {
  total_budget: number;
  total_actual: number;
  total_forecast: number;
  variance: number;
  variance_pct: number | null;
  budget_utilization_pct: number | null;
}

export interface MonthlyData {
  month: string;
  budget: number;
  actual: number;
  forecast?: number;
}

export interface CumulativeData {
  month: string;
  cumulative_budget: number;
  cumulative_actual: number;
}

export interface BurnRateData {
  month: string;
  monthly_spend: number;
  avg_monthly_spend: number;
  remaining_budget: number;
}

export interface TopItem {
  name: string;
  code: string | null;
  amount: number;
  percentage: number | null;
}

export interface LancamentoItem {
  id: string;
  data_lancamento: string;
  conta_contabil_numero: string;
  conta_contabil_nome: string;
  centro_de_custo_codigo: string;
  centro_de_custo_nome: string;
  fonte: string;
  valor: number;
  observacao: string | null;
  nome_conta_contrapartida: string | null;
}

export interface LancamentoListResponse {
  items: LancamentoItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface BudgetPlanilhaRow {
  centro_de_custo_codigo: string;
  centro_de_custo_nome: string;
  conta_contabil_numero: string;
  conta_contabil_nome: string;
  conta_agrupamento: string | null;
  conta_dre: string | null;
  budget_jan: number; budget_fev: number; budget_mar: number;
  budget_abr: number; budget_mai: number; budget_jun: number;
  budget_jul: number; budget_ago: number; budget_set: number;
  budget_out: number; budget_nov: number; budget_dez: number;
  budget_total: number;
  razao_jan: number; razao_fev: number; razao_mar: number;
  razao_abr: number; razao_mai: number; razao_jun: number;
  razao_jul: number; razao_ago: number; razao_set: number;
  razao_out: number; razao_nov: number; razao_dez: number;
  razao_total: number;
}

export interface BudgetPlanilhaResponse {
  rows: BudgetPlanilhaRow[];
  total_rows: number;
}

// ---- API helpers ----

export const dashboardApi = {
  getKpis: (year: number) => api.get<DashboardKPIs>("/dashboard/kpis", { year }),
  getBudgetVsActual: (year: number) => api.get<MonthlyData[]>("/dashboard/charts/budget-vs-actual", { year }),
  getCumulative: (year: number) => api.get<CumulativeData[]>("/dashboard/charts/cumulative", { year }),
  getBurnRate: (year: number) => api.get<BurnRateData[]>("/dashboard/charts/burn-rate", { year }),
  getTopCostCenters: (year: number, top_n = 10) => api.get<TopItem[]>("/dashboard/charts/top-cost-centers", { year, top_n }),
  getTopExpenses: (year: number, top_n = 10) => api.get<TopItem[]>("/dashboard/charts/top-expenses", { year, top_n }),
};

export const lancamentosApi = {
  list: (params: { year: number; month?: number; fonte?: string; page?: number; page_size?: number }) =>
    api.get<LancamentoListResponse>("/lancamentos/", params as Record<string, string | number | undefined>),
  getPlanilha: (year: number, centro_de_custo_id?: string, departamento_id?: string) =>
    api.get<BudgetPlanilhaResponse>("/lancamentos/planilha", { year, centro_de_custo_id, departamento_id }),
  getCentrosDeCusto: () =>
    api.get<{ id: string; codigo: string; nome: string }[]>("/lancamentos/centros-de-custo"),
  getContasContabeis: () =>
    api.get<{ id: string; numero: string; nome: string; dre: string }[]>("/lancamentos/contas-contabeis"),
};
