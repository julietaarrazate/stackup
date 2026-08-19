/** Server-side session helpers used by server components. */
import "server-only";
import { apiFetchWithSession } from "@/lib/api";

export type CurrentUser = {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
};

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  base_currency: string;
  timezone: string;
};

export type Application = {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: "active" | "archived";
  production_url: string | null;
  repository_url: string | null;
};

export type Cost = {
  id: string;
  application_id: string;
  service_id: string;
  environment_id: string | null;
  name: string;
  category: string | null;
  billing_type: "fixed" | "usage" | "one_time";
  amount: string;
  currency: string;
  frequency: "weekly" | "monthly" | "quarterly" | "yearly" | "custom";
  status: "active" | "paused" | "ended";
  certainty: "confirmed" | "estimated" | "projected";
  monthly_equivalent: string;
  annualized_cost: string;
};

/** Returns the authenticated user, or null if there is no valid session. */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  const res = await apiFetchWithSession("/api/v1/users/me");
  if (!res.ok) return null;
  return (await res.json()) as CurrentUser;
}

export async function listWorkspaces(): Promise<Workspace[]> {
  const res = await apiFetchWithSession("/api/v1/workspaces");
  if (!res.ok) return [];
  return (await res.json()) as Workspace[];
}

export async function getWorkspace(id: string): Promise<Workspace | null> {
  const res = await apiFetchWithSession(`/api/v1/workspaces/${id}`);
  if (!res.ok) return null;
  return (await res.json()) as Workspace;
}

export async function listApplications(
  workspaceId: string,
): Promise<Application[]> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/applications`,
  );
  if (!res.ok) return [];
  return (await res.json()) as Application[];
}

export async function listCosts(workspaceId: string): Promise<Cost[]> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/costs`,
  );
  if (!res.ok) return [];
  return (await res.json()) as Cost[];
}

export type Vendor = {
  id: string;
  name: string;
  is_global: boolean;
};

export type CurrencyTotal = {
  currency: string;
  monthly: string;
  annualized: string;
};
export type GroupTotal = {
  label: string;
  currency: string;
  monthly: string;
  annualized: string;
};
export type CertaintyTotal = {
  certainty: string;
  currency: string;
  monthly: string;
};
export type RecentChange = {
  cost_id: string;
  cost_name: string;
  amount: string;
  currency: string;
  effective_from: string;
  reason: string | null;
};
export type OverviewReport = {
  total: CurrencyTotal[];
  by_certainty: CertaintyTotal[];
  by_category: GroupTotal[];
  by_vendor: GroupTotal[];
  by_application: GroupTotal[];
  recent_changes: RecentChange[];
  cost_item_count: number;
};
export type EvolutionPoint = { period: string; currency: string; monthly: string };
export type EvolutionReport = { points: EvolutionPoint[] };

export type Expense = {
  id: string;
  cost_item_id: string;
  amount: string;
  currency: string;
  paid_at: string | null;
  status: "pending" | "paid" | "failed" | "refunded";
  invoice_number: string | null;
  evidence_id: string | null;
};

export async function listVendors(workspaceId: string): Promise<Vendor[]> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/vendors`,
  );
  if (!res.ok) return [];
  return (await res.json()) as Vendor[];
}

export async function getOverview(
  workspaceId: string,
): Promise<OverviewReport | null> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/reports/overview`,
  );
  if (!res.ok) return null;
  return (await res.json()) as OverviewReport;
}

export async function getEvolution(
  workspaceId: string,
): Promise<EvolutionReport> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/reports/evolution?months=6`,
  );
  if (!res.ok) return { points: [] };
  return (await res.json()) as EvolutionReport;
}

export async function listExpenses(workspaceId: string): Promise<Expense[]> {
  const res = await apiFetchWithSession(
    `/api/v1/workspaces/${workspaceId}/expenses`,
  );
  if (!res.ok) return [];
  return (await res.json()) as Expense[];
}
