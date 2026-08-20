import type { Metadata } from "next";
import { listVendors } from "@/lib/session";
import { VendorsExplorer } from "@/components/vendors-explorer";

export const metadata: Metadata = { title: "Proveedores" };

export default async function VendorsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const vendors = await listVendors(workspaceId);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Proveedores</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Catálogo global compartido más los proveedores propios de este
          workspace, con sus servicios.
        </p>
      </div>

      <VendorsExplorer workspaceId={workspaceId} vendors={vendors} />
    </div>
  );
}
