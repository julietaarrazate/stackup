import type { Metadata } from "next";
import {
  getGithubConnection,
  listApplications,
  listDetections,
  listVendors,
} from "@/lib/session";
import { GitHubIntegration } from "@/components/github-integration";
import { DetectionsList } from "@/components/detections-list";

export const metadata: Metadata = { title: "Integraciones" };

export default async function IntegrationsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [connection, applications, vendors, detections] = await Promise.all([
    getGithubConnection(workspaceId),
    listApplications(workspaceId),
    listVendors(workspaceId),
    listDetections(workspaceId, "pending"),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Integraciones</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Conectá GitHub para detectar automáticamente proveedores que ya
          estás pagando. Nunca se crea un costo sin que lo confirmes vos.
        </p>
      </div>

      <GitHubIntegration
        workspaceId={workspaceId}
        connection={connection}
        applications={applications}
      />

      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold tracking-tight">
          Detecciones pendientes
        </h2>
        <DetectionsList
          workspaceId={workspaceId}
          detections={detections}
          applications={applications}
          vendors={vendors}
        />
      </div>
    </div>
  );
}
