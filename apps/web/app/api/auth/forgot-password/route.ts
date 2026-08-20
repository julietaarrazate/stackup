import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/** BFF: request a password-reset email. Always accepted (no user enumeration). */
export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyToBackend("/api/v1/auth/forgot-password", {
    method: "POST",
    contentType: "application/json",
    body,
  });
}
