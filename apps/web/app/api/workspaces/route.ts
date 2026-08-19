import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/** BFF: list the current user's workspaces. */
export async function GET() {
  return proxyToBackend("/api/v1/workspaces", { method: "GET" });
}

/** BFF: create a workspace. */
export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyToBackend("/api/v1/workspaces", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
