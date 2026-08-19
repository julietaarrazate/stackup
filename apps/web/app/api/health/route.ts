import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

/**
 * BFF health proxy: the browser hits this same-origin route, which checks the
 * backend server-side. Demonstrates the BFF wiring end-to-end without ever
 * exposing the FastAPI URL to the client.
 */
export async function GET() {
  try {
    const res = await apiFetch("/ready");
    const body = (await res.json()) as unknown;
    return NextResponse.json(
      { frontend: "ok", backend: body },
      { status: res.ok ? 200 : 503 },
    );
  } catch {
    return NextResponse.json(
      { frontend: "ok", backend: "unreachable" },
      { status: 503 },
    );
  }
}
