import type { Metadata } from "next";
import { getCurrentUser, listMembers } from "@/lib/session";
import { MembersManager } from "@/components/members-manager";

export const metadata: Metadata = { title: "Miembros" };

export default async function MembersPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [members, user] = await Promise.all([
    listMembers(workspaceId),
    getCurrentUser(),
  ]);
  if (!user) return null;

  const myRole = members.find((m) => m.user_id === user.id)?.role;
  const canManage = myRole === "owner" || myRole === "admin";
  const isOwner = myRole === "owner";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Miembros</h1>
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
  );
}
