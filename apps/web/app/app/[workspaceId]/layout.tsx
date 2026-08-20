import { notFound, redirect } from "next/navigation";
import { getCurrentUser, getWorkspace, listWorkspaces } from "@/lib/session";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function WorkspaceLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const [workspace, workspaces] = await Promise.all([
    getWorkspace(workspaceId),
    listWorkspaces(),
  ]);
  if (!workspace) notFound();

  return (
    <WorkspaceShell
      workspace={workspace}
      workspaces={workspaces}
      userName={user.full_name || user.email}
    >
      {children}
    </WorkspaceShell>
  );
}
