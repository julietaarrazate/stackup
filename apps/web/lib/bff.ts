/**
 * BFF helpers shared by the proxy route handlers: forward the request cookies
 * to FastAPI and relay the response (including Set-Cookie) back to the browser,
 * so the session cookie is issued/cleared by the backend but travels through
 * our first-party origin. Content-type agnostic: forwards JSON, multipart
 * uploads, and binary downloads alike.
 */
import "server-only";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

const PASSTHROUGH_HEADERS = [
  "content-type",
  "content-disposition",
  "cache-control",
];

export async function proxyToBackend(
  path: string,
  init: RequestInit & { contentType?: string | null },
): Promise<NextResponse> {
  const cookieHeader = (await cookies()).toString();
  const { contentType, headers, ...rest } = init;
  const backendRes = await apiFetch(path, {
    ...rest,
    cookie: cookieHeader,
    headers: {
      ...(contentType ? { "content-type": contentType } : {}),
      ...headers,
    },
  });

  const buffer = await backendRes.arrayBuffer();
  const outHeaders = new Headers();
  for (const name of PASSTHROUGH_HEADERS) {
    const value = backendRes.headers.get(name);
    if (value) outHeaders.set(name, value);
  }
  const res = new NextResponse(buffer.byteLength ? buffer : null, {
    status: backendRes.status,
    headers: outHeaders,
  });
  for (const value of backendRes.headers.getSetCookie()) {
    res.headers.append("set-cookie", value);
  }
  return res;
}
