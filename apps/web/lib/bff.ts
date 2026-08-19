/**
 * BFF helpers shared by auth route handlers: forward the request cookies to
 * FastAPI and relay any Set-Cookie back to the browser, so the session cookie
 * is issued/cleared by the backend but travels through our first-party origin.
 */
import "server-only";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

/** Call the backend forwarding current cookies, relaying Set-Cookie out. */
export async function proxyToBackend(
  path: string,
  init: RequestInit,
): Promise<NextResponse> {
  const cookieHeader = (await cookies()).toString();
  const backendRes = await apiFetch(path, { ...init, cookie: cookieHeader });

  const bodyText = await backendRes.text();
  const contentType = backendRes.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  const res = new NextResponse(bodyText || null, {
    status: backendRes.status,
    headers: isJson ? { "content-type": "application/json" } : undefined,
  });

  // Relay each Set-Cookie header from the backend to the browser.
  for (const value of backendRes.headers.getSetCookie()) {
    res.headers.append("set-cookie", value);
  }
  return res;
}
