import { NextRequest, NextResponse } from "next/server";
import { apiFetchWithSession } from "@/lib/api";

/**
 * GitHub's OAuth redirect_uri — a single fixed URL (no workspace id in the
 * path). Forwards {code, state} to the backend, which recovers the
 * workspace from the signed state and completes the connection, then
 * redirects the browser to that workspace's Integrations page.
 */
export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");
  const state = req.nextUrl.searchParams.get("state");
  if (!code || !state) {
    return NextResponse.redirect(new URL("/app?github_error=1", req.url));
  }

  const res = await apiFetchWithSession("/api/v1/integrations/github/callback", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code, state }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL("/app?github_error=1", req.url));
  }
  const connection = (await res.json()) as { workspace_id: string };
  return NextResponse.redirect(
    new URL(`/app/${connection.workspace_id}/integrations`, req.url),
  );
}
