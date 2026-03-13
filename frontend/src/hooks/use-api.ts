import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

// Dashboard
export function useDashboardKPIs(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["dashboard-kpis", params],
    queryFn: () => api.get("/dashboard/kpis", params),
  });
}

export function useBudgetVsActualChart(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["chart-budget-vs-actual", params],
    queryFn: () => api.get("/dashboard/charts/budget-vs-actual", params),
  });
}

export function useCumulativeChart(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["chart-cumulative", params],
    queryFn: () => api.get("/dashboard/charts/cumulative", params),
  });
}

export function useBurnRateChart(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["chart-burn-rate", params],
    queryFn: () => api.get("/dashboard/charts/burn-rate", params),
  });
}

export function useTopCostCenters(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["chart-top-cost-centers", params],
    queryFn: () => api.get("/dashboard/charts/top-cost-centers", params),
  });
}

export function useTopExpenses(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["chart-top-expenses", params],
    queryFn: () => api.get("/dashboard/charts/top-expenses", params),
  });
}

// Budget Versions
export function useBudgetVersions(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["budget-versions", params],
    queryFn: () => api.get("/budget-versions", params),
  });
}

// Budget Spreadsheet
export function useBudgetSpreadsheet(versionId: string | null) {
  return useQuery({
    queryKey: ["budget-spreadsheet", versionId],
    queryFn: () => api.get(`/budgets/spreadsheet/${versionId}`),
    enabled: !!versionId,
  });
}

// Budget mutations
export function useUpdateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.put(`/budgets/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget-spreadsheet"] });
    },
  });
}

// Actuals
export function useActuals(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["actuals", params],
    queryFn: () => api.get("/actuals", params),
  });
}

// Forecasts
export function useForecasts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["forecasts", params],
    queryFn: () => api.get("/forecasts", params),
  });
}

export function useGenerateForecast() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post("/forecasts/generate", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["forecasts"] });
    },
  });
}

// Cost Centers
export function useCostCenters(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["cost-centers", params],
    queryFn: () => api.get("/cost-centers", params),
  });
}

// Accounts
export function useAccounts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["accounts", params],
    queryFn: () => api.get("/accounts", params),
  });
}

// Users
export function useUsers(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => api.get("/users", params),
  });
}
