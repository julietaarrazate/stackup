import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/**
 * Catch-all BFF proxy for authenticated data calls. The browser calls
 * /api/v1/<anything> same-origin; this forwards it to FastAPI's /api/v1/<anything>
 * with the session cookie attached, relaying Set-Cookie back. The backend
 * enforces all authorization — this proxy only forwards the session, it never
 * widens access. Auth endpoints keep their own explicit handlers.
 */
async function handle(req: NextRequest, path: string[]) {
  const suffix = path.join("/");
  const search = req.nextUrl.search;
  const method = req.method;
  const hasBody = method !== "GET" && method !== "HEAD";
  // Forward the raw body and original content-type so JSON, multipart uploads
  // and any other payload pass through unchanged.
  const body = hasBody ? await req.arrayBuffer() : undefined;
  return proxyToBackend(`/api/v1/${suffix}${search}`, {
    method,
    contentType: hasBody ? req.headers.get("content-type") : undefined,
    body,
  });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  return handle(req, (await ctx.params).path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  return handle(req, (await ctx.params).path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  return handle(req, (await ctx.params).path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  return handle(req, (await ctx.params).path);
}
