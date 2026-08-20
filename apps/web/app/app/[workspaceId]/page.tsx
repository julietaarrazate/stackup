import Link from "next/link";
import type { Metadata } from "next";
import { getEvolution, getOverview, getWorkspace, listApplications } from "@/lib/session";
import { Dashboard } from "@/components/dashboard";

export const metadata: Metadata = { title: "Overview" };

export default async function WorkspaceOverview({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [workspace, applications, overview, evolution] = await Promise.all([
    getWorkspace(workspaceId),
    listApplications(workspaceId),
    getOverview(workspaceId),
    getEvolution(workspaceId),
  ]);
  if (!workspace) return null;

  const hasData = overview && overview.cost_item_count > 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Cuánto te cuesta realmente mantener {workspace.name}.
        </p>
      </div>

      {hasData ? (
        <Dashboard overview={overview} evolution={evolution} baseCurrency={workspace.base_currency} />
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Todavía no hay costos cargados</p>
          <p className="max-w-sm text-sm text-[var(--muted-foreground)]">
            {applications.length === 0
              ? "Agregá tu primera aplicación y después cargale costos para ver el panorama completo acá."
              : "Cargá el primer costo de una aplicación para ver el total mensual, la evolución y el desglose."}
          </p>
          <Link
            href={
              applications.length === 0
                ? `/app/${workspaceId}/applications`
                : `/app/${workspaceId}/costs`
            }
            className="mt-1 inline-flex items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90"
          >
            {applications.length === 0 ? "Agregar aplicación" : "Agregar costo"}
          </Link>
        </div>
      )}
    </div>
  );
}
