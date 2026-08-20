import type { Metadata } from "next";
import { getCurrentUser, getWorkspace, listMembers } from "@/lib/session";
import { WorkspaceSettingsForm } from "@/components/workspace-settings-form";
import { MembersManager } from "@/components/members-manager";

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
  const isOwner = myRole === "owner";

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ajustes</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Datos del workspace y miembros con acceso.
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

      <div className="flex flex-col gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Miembros</h2>
          <p className="text-sm text-[var(--muted-foreground)]">
            {canManage
              ? "Agregá personas que ya tengan cuenta en STACKUP y asigná su rol."
              : "Quiénes tienen acceso a este workspace."}
          </p>
        </div>
        <MembersManager
          workspaceId={workspaceId}
          members={members}
          currentUserId={user.id}
          canManage={canManage}
          isOwner={isOwner}
        />
      </div>
    </div>
  );
}
