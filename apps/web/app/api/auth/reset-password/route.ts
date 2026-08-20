import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/** BFF: reset the password using a token from the email link. */
export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyToBackend("/api/v1/auth/reset-password", {
    method: "POST",
    contentType: "application/json",
    body,
  });
}
