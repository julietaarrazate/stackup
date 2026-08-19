import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff";

/**
 * BFF login. Accepts JSON {email, password} from the browser and forwards it
 * to FastAPI's OAuth2 form-encoded login, relaying the session cookie back.
 */
export async function POST(req: NextRequest) {
  const { email, password } = (await req.json()) as {
    email?: string;
    password?: string;
  };
  const form = new URLSearchParams();
  form.set("username", email ?? "");
  form.set("password", password ?? "");

  return proxyToBackend("/api/v1/auth/login", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
}
