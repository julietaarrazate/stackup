import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/** BFF register. Forwards {email, password} JSON to FastAPI. */
export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyToBackend("/api/v1/auth/register", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
