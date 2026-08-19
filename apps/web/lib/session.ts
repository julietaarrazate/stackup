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
