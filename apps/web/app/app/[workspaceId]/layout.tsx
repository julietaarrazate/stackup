import { notFound, redirect } from "next/navigation";
import { getCurrentUser, getWorkspace } from "@/lib/session";
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

  const workspace = await getWorkspace(workspaceId);
  if (!workspace) notFound();

  return (
    <WorkspaceShell workspace={workspace} userEmail={user.email}>
      {children}
    </WorkspaceShell>
  );
}
