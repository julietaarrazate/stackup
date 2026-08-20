import Link from "next/link";
import type { Metadata } from "next";
import { listApplications, listCosts, listExpenses, listVendors } from "@/lib/session";
import { CreateCost } from "@/components/create-cost";
import { CostsList } from "@/components/costs-list";
import { RecordExpense } from "@/components/record-expense";
import { formatMoney, formatDate } from "@/lib/format";

export const metadata: Metadata = { title: "Costos" };

export default async function CostsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const [applications, vendors, costs, expenses] = await Promise.all([
    listApplications(workspaceId),
    listVendors(workspaceId),
    listCosts(workspaceId),
    listExpenses(workspaceId),
  ]);
  const appName = new Map(applications.map((a) => [a.id, a.name]));
  const costName = new Map(costs.map((c) => [c.id, c.name]));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Costos</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Todos los costos del workspace, con su equivalente mensual y anual.
        </p>
      </div>

      {applications.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Creá una aplicación primero</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Los costos se registran dentro de una aplicación.
          </p>
          <Link
            href={`/app/${workspaceId}/applications`}
            className="mt-4 inline-flex items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90"
          >
            Ir a Aplicaciones
          </Link>
        </div>
      ) : (
        <CreateCost workspaceId={workspaceId} applications={applications} vendors={vendors} />
      )}

      {costs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Sin costos todavía</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Agregá el primer costo para ver su equivalente mensual y anual.
          </p>
        </div>
      ) : (
        <CostsList workspaceId={workspaceId} costs={costs} appName={appName} />
      )}

      {costs.length > 0 ? (
        <section className="flex flex-col gap-4 border-t border-[var(--border)] pt-6">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">
              Pagos y comprobantes
            </h2>
            <p className="text-sm text-[var(--muted-foreground)]">
              Registrá cada pago efectivamente realizado, con su comprobante.
            </p>
          </div>
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
                      {e.paid_at ? formatDate(e.paid_at) : "sin fecha"}
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
    </div>
  );
}
