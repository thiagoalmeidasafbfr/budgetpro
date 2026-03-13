export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "manager" | "analyst" | "viewer";
  department?: string;
  avatar?: string;
  status: "active" | "inactive";
  createdAt: string;
}

export interface CostCenter {
  id: string;
  code: string;
  name: string;
  parentId?: string;
  responsible: string;
  department: string;
  company: string;
  budget: number;
  actual: number;
  variance: number;
  children?: CostCenter[];
}

export interface Account {
  id: string;
  code: string;
  name: string;
  category: string;
  type: "expense" | "revenue" | "investment";
}

export interface BudgetRow {
  id: string;
  costCenterId: string;
  costCenterName: string;
  costCenterCode: string;
  accountId: string;
  accountName: string;
  accountCode: string;
  category: string;
  jan: number;
  feb: number;
  mar: number;
  apr: number;
  may: number;
  jun: number;
  jul: number;
  aug: number;
  sep: number;
  oct: number;
  nov: number;
  dec: number;
  total: number;
}

export interface ActualEntry {
  id: string;
  date: string;
  costCenterId: string;
  costCenterName: string;
  accountId: string;
  accountName: string;
  category: string;
  description: string;
  amount: number;
  document?: string;
  status: "pending" | "approved" | "rejected";
}

export interface ForecastRow extends BudgetRow {
  method: "linear" | "moving_avg" | "manual" | "seasonal";
}

export interface BudgetVersion {
  id: string;
  name: string;
  year: number;
  status: "draft" | "review" | "approved" | "locked";
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  description?: string;
  totalBudget: number;
}

export interface KPIData {
  label: string;
  value: number;
  previousValue: number;
  change: number;
  changeType: "positive" | "negative" | "neutral";
  sparkline: number[];
}

export interface MonthlyData {
  month: string;
  budget: number;
  actual: number;
  forecast?: number;
}

export interface CostCenterSummary {
  name: string;
  code: string;
  budget: number;
  actual: number;
  variance: number;
  percentage: number;
}

export interface ExpenseCategory {
  name: string;
  value: number;
  percentage: number;
  color: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
  read: boolean;
  createdAt: string;
}

export interface FilterState {
  year: number;
  company: string;
  department: string;
  costCenter: string;
  category: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  total?: number;
  page?: number;
  pageSize?: number;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}
