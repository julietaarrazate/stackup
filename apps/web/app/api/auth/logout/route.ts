import { proxyToBackend } from "@/lib/bff";

/** BFF logout. Forwards to FastAPI, which revokes the session and clears the cookie. */
export async function POST() {
  return proxyToBackend("/api/v1/auth/logout", { method: "POST" });
}
