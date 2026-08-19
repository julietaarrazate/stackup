/**
 * Server-side API client (the BFF layer, ADR-001/003).
 *
 * Only ever imported from server components and route handlers — never from
 * client components. Reads the FastAPI base URL from the environment (never a
 * hardcoded production URL) and forwards the caller's cookies so FastAPI can
 * resolve the session. The browser never talks to FastAPI directly and never
 * sees the backend URL or any secret.
 */
import "server-only";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function apiFetch(
  path: string,
  init?: RequestInit & { cookie?: string },
): Promise<Response> {
  const { cookie, headers, ...rest } = init ?? {};
  return fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      ...(cookie ? { cookie } : {}),
      ...headers,
    },
    cache: "no-store",
  });
}

/** apiFetch with the current request's cookies forwarded automatically. */
export async function apiFetchWithSession(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const cookieHeader = (await cookies()).toString();
  return apiFetch(path, { ...init, cookie: cookieHeader });
}

export function apiBaseUrl(): string {
  return API_BASE_URL;
}
