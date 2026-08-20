import Link from "next/link";
import type { Metadata } from "next";
import { ChevronRight } from "lucide-react";
import { getOverview, listApplications } from "@/lib/session";
import { CreateApplication } from "@/components/create-application";
import { formatMoney } from "@/lib/format";

export const metadata: Metadata = { title: "Aplicaciones" };

export default async function ApplicationsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [applications, overview] = await Promise.all([
    listApplications(workspaceId),
    getOverview(workspaceId),
  ]);

  const costByApp = new Map(
    (overview?.by_application ?? []).map((g) => [g.label, g]),
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Aplicaciones</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Cada aplicación agrupa sus environments, servicios y costos.
        </p>
      </div>

      <CreateApplication workspaceId={workspaceId} />

      {applications.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Sin aplicaciones todavía</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Agregá una aplicación para empezar a registrar sus costos.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {applications.map((app) => {
            const cost = costByApp.get(app.name);
            return (
              <li key={app.id}>
                <Link
                  href={`/app/${workspaceId}/applications/${app.id}`}
                  className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3.5 transition-colors hover:bg-[var(--surface-2)]"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">{app.name}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      /{app.slug}
                      {app.status !== "active" ? " · archivada" : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {cost ? (
                      <span className="tabular text-sm font-semibold">
                        {formatMoney(cost.monthly, cost.currency)}/mes
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--muted-foreground)]">
                        sin costos
                      </span>
                    )}
                    <ChevronRight className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
