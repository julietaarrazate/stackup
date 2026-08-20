import Link from "next/link";
import type { Metadata } from "next";
import { Users } from "lucide-react";
import { getCurrentUser, getWorkspace, listMembers } from "@/lib/session";
import { WorkspaceSettingsForm } from "@/components/workspace-settings-form";

export const metadata: Metadata = { title: "Ajustes" };

export default async function SettingsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [workspace, members, user] = await Promise.all([
    getWorkspace(workspaceId),
    listMembers(workspaceId),
    getCurrentUser(),
  ]);
  if (!workspace || !user) return null;

  const myRole = members.find((m) => m.user_id === user.id)?.role;
  const canManage = myRole === "owner" || myRole === "admin";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ajustes</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Datos del workspace.
        </p>
      </div>

      {canManage ? (
        <WorkspaceSettingsForm workspace={workspace} />
      ) : (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-sm">
          <p className="font-medium">{workspace.name}</p>
          <p className="text-[var(--muted-foreground)]">
            /{workspace.slug} · {workspace.base_currency}
          </p>
        </div>
      )}

      <Link
        href={`/app/${workspaceId}/members`}
        className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3.5 transition-colors hover:bg-[var(--surface-2)]"
      >
        <span className="flex items-center gap-3">
          <Users className="h-4 w-4 text-[var(--muted-foreground)]" />
          <span>
            <span className="block font-medium">Miembros</span>
            <span className="block text-xs text-[var(--muted-foreground)]">
              {members.length} con acceso a este workspace
            </span>
          </span>
        </span>
      </Link>
    </div>
  );
}
