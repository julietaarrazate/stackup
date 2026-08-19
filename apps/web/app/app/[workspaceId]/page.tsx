import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowLeft } from "lucide-react";
import {
  getEvolution,
  getOverview,
  getWorkspace,
  listApplications,
  listCosts,
  listExpenses,
  listVendors,
} from "@/lib/session";
import { BrandWordmark } from "@/components/brand";
import { CreateApplication } from "@/components/create-application";
import { CreateCost } from "@/components/create-cost";
import { Dashboard } from "@/components/dashboard";
import { RecordExpense } from "@/components/record-expense";
import { formatMoney } from "@/lib/format";

export const metadata: Metadata = { title: "Workspace" };

const FREQUENCY_LABEL: Record<string, string> = {
  weekly: "semanal",
  monthly: "mensual",
  quarterly: "trimestral",
  yearly: "anual",
  custom: "custom",
};

export default async function WorkspaceDetail({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const workspace = await getWorkspace(workspaceId);
  if (!workspace) notFound();

  const [applications, vendors, costs, overview, evolution, expenses] =
    await Promise.all([
      listApplications(workspaceId),
      listVendors(workspaceId),
      listCosts(workspaceId),
      getOverview(workspaceId),
      getEvolution(workspaceId),
      listExpenses(workspaceId),
    ]);
  const costName = new Map(costs.map((c) => [c.id, c.name]));

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

      {overview && overview.cost_item_count > 0 ? (
        <section className="py-2">
          <Dashboard
            overview={overview}
            evolution={evolution}
            baseCurrency={workspace.base_currency}
          />
        </section>
      ) : null}

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
                  <p className="text-xs text-[var(--muted-foreground)]">/{app.slug}</p>
                </div>
                <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]">
                  {app.status === "active" ? "activa" : "archivada"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-4 py-4">
        <h2 className="text-lg font-semibold tracking-tight">Costos</h2>
        {applications.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">
            Creá una aplicación primero para poder cargar costos.
          </p>
        ) : (
          <CreateCost
            workspaceId={workspaceId}
            applications={applications}
            vendors={vendors}
          />
        )}

        {costs.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
            <p className="font-medium">Sin costos todavía</p>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              Agregá el primer costo para ver su equivalente mensual y anual.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {costs.map((c) => (
              <li
                key={c.id}
                className="tabular flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
              >
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {formatMoney(c.amount, c.currency)} ·{" "}
                    {FREQUENCY_LABEL[c.frequency] ?? c.frequency}
                    {c.category ? ` · ${c.category}` : ""}
                    {c.certainty !== "confirmed" ? ` · ${c.certainty}` : ""}
                    {c.status !== "active" ? ` · ${c.status}` : ""}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">
                    {formatMoney(c.monthly_equivalent, c.currency)}/mes
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {formatMoney(c.annualized_cost, c.currency)} anual
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {costs.length > 0 ? (
        <section className="flex flex-col gap-4 py-4">
          <h2 className="text-lg font-semibold tracking-tight">
            Pagos y comprobantes
          </h2>
          <RecordExpense workspaceId={workspaceId} costs={costs} />
          {expenses.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {expenses.map((e) => (
                <li
                  key={e.id}
                  className="tabular flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
                >
                  <div>
                    <p className="font-medium">
                      {costName.get(e.cost_item_id) ?? "Costo"}
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {e.paid_at ?? "sin fecha"}
                      {e.invoice_number ? ` · ${e.invoice_number}` : ""}
                      {e.evidence_id ? " · 📎 comprobante" : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">
                      {formatMoney(e.amount, e.currency)}
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {e.status}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <footer className="mt-auto border-t border-[var(--border)] py-6 text-sm text-[var(--muted-foreground)]">
        Background jobs e integración con GitHub llegan en las próximas fases.
      </footer>
    </main>
  );
}
