import type { Metadata } from "next";
import { getEvolution, getOverview, listApplications } from "@/lib/session";
import { ReportsExplorer } from "@/components/reports-explorer";

export const metadata: Metadata = { title: "Reportes" };

export default async function ReportsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [applications, overview, evolution] = await Promise.all([
    listApplications(workspaceId),
    getOverview(workspaceId),
    getEvolution(workspaceId, 6),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reportes</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Analizá la evolución del costo y su distribución por aplicación,
          proveedor y categoría.
        </p>
      </div>

      <ReportsExplorer
        workspaceId={workspaceId}
        applications={applications}
        initialOverview={overview}
        initialEvolution={evolution}
      />
    </div>
  );
}
