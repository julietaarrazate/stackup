import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowLeft } from "lucide-react";
import { getWorkspace, listApplications } from "@/lib/session";
import { BrandWordmark } from "@/components/brand";
import { CreateApplication } from "@/components/create-application";

export const metadata: Metadata = { title: "Workspace" };

export default async function WorkspaceDetail({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const workspace = await getWorkspace(workspaceId);
  if (!workspace) notFound();

  const applications = await listApplications(workspaceId);

  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <BrandWordmark />
        <Link
          href="/app"
          className="inline-flex items-center gap-1 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Workspaces
        </Link>
      </header>

      <section className="py-4">
        <h1 className="text-2xl font-semibold tracking-tight">{workspace.name}</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          /{workspace.slug} · moneda base {workspace.base_currency}
        </p>
      </section>

      <section className="flex flex-col gap-4 py-4">
        <h2 className="text-lg font-semibold tracking-tight">Aplicaciones</h2>
        <CreateApplication workspaceId={workspaceId} />

        {applications.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
            <p className="font-medium">Sin aplicaciones todavía</p>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              Agregá una aplicación para empezar a registrar sus costos.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {applications.map((app) => (
              <li
                key={app.id}
                className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
              >
                <div>
                  <p className="font-medium">{app.name}</p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    /{app.slug}
                    {app.repository_url ? ` · ${app.repository_url}` : ""}
                  </p>
                </div>
                <span
                  className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]"
                  data-status={app.status}
                >
                  {app.status === "active" ? "activa" : "archivada"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="mt-auto border-t border-[var(--border)] py-6 text-sm text-[var(--muted-foreground)]">
        Environments, vendors y costos se gestionan desde acá en las próximas fases.
      </footer>
    </main>
  );
}
