import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowLeft } from "lucide-react";
import {
  getApplication,
  getOverview,
  listApplications,
  listCosts,
  listEnvironments,
  listVendors,
} from "@/lib/session";
import { ApplicationTabs } from "@/components/application-tabs";
import { EntityIcon } from "@/components/entity-icon";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ workspaceId: string; applicationId: string }>;
}): Promise<Metadata> {
  const { workspaceId, applicationId } = await params;
  const app = await getApplication(workspaceId, applicationId);
  return { title: app?.name ?? "Aplicación" };
}

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ workspaceId: string; applicationId: string }>;
}) {
  const { workspaceId, applicationId } = await params;

  const application = await getApplication(workspaceId, applicationId);
  if (!application) notFound();

  const [applications, vendors, allCosts, environments, overview] =
    await Promise.all([
      listApplications(workspaceId),
      listVendors(workspaceId),
      listCosts(workspaceId),
      listEnvironments(workspaceId, applicationId),
      getOverview(workspaceId, { applicationId }),
    ]);

  const costs = allCosts.filter((c) => c.application_id === applicationId);

  return (
    <div className="flex flex-col gap-6">
      <Link
        href={`/app/${workspaceId}/applications`}
        className="inline-flex w-fit items-center gap-1 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
      >
        <ArrowLeft className="h-4 w-4" />
        Aplicaciones
      </Link>

      <div>
        <div className="flex items-center gap-3">
          <EntityIcon name={application.name} />
          <h1 className="text-2xl font-semibold tracking-tight">
            {application.name}
          </h1>
          {application.status !== "active" ? (
            <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]">
              archivada
            </span>
          ) : null}
        </div>
        {application.description ? (
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            {application.description}
          </p>
        ) : null}
        {application.repository_url ? (
          <a
            href={application.repository_url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-block text-sm text-[var(--primary)] hover:underline"
          >
            {application.repository_url}
          </a>
        ) : null}
      </div>

      <ApplicationTabs
        workspaceId={workspaceId}
        application={application}
        applications={applications}
        vendors={vendors}
        costs={costs}
        environments={environments}
        totals={overview?.total ?? []}
        byCategory={overview?.by_category ?? []}
        byVendor={overview?.by_vendor ?? []}
        byCertainty={overview?.by_certainty ?? []}
        recentChanges={overview?.recent_changes ?? []}
      />
    </div>
  );
}
