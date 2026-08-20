"use client";

import { useState } from "react";
import { CategoryDonut, CATEGORY_COLORS } from "./dashboard-charts";
import { CreateCost } from "./create-cost";
import { CreateEnvironment } from "./create-environment";
import { formatMoney } from "@/lib/format";
import type {
  Application,
  CertaintyTotal,
  Cost,
  CurrencyTotal,
  Environment,
  GroupTotal,
  RecentChange,
  Vendor,
} from "@/lib/session";

const FREQUENCY_LABEL: Record<string, string> = {
  weekly: "semanal",
  monthly: "mensual",
  quarterly: "trimestral",
  yearly: "anual",
  custom: "custom",
};

const ENV_TYPE_LABEL: Record<string, string> = {
  production: "producción",
  staging: "staging",
  development: "desarrollo",
  preview: "preview",
  other: "otro",
};

type Tab = "overview" | "costs" | "environments" | "history";

function primaryCurrency(totals: CurrencyTotal[]): string | null {
  if (totals.length === 0) return null;
  const sorted = [...totals].sort(
    (a, b) => Number(b.monthly) - Number(a.monthly),
  );
  return sorted[0]?.currency ?? null;
}

export function ApplicationTabs({
  workspaceId,
  application,
  applications,
  vendors,
  costs,
  environments,
  totals,
  byCategory,
  byVendor,
  byCertainty,
  recentChanges,
}: {
  workspaceId: string;
  application: Application;
  applications: Application[];
  vendors: Vendor[];
  costs: Cost[];
  environments: Environment[];
  totals: CurrencyTotal[];
  byCategory: GroupTotal[];
  byVendor: GroupTotal[];
  byCertainty: CertaintyTotal[];
  recentChanges: RecentChange[];
}) {
  const [tab, setTab] = useState<Tab>("overview");
  const cur = primaryCurrency(totals);
  const total = totals.find((t) => t.currency === cur);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Resumen" },
    { id: "costs", label: "Costos" },
    { id: "environments", label: "Entornos" },
    { id: "history", label: "Historial" },
  ];

  return (
    <div className="flex flex-col gap-5">
      <div className="flex gap-1 overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            aria-current={tab === t.id ? "page" : undefined}
            className={`flex-1 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" ? (
        <div className="flex flex-col gap-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="text-xs text-[var(--muted-foreground)]">
                Costo mensual{cur ? ` (${cur})` : ""}
              </p>
              <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
                {total ? formatMoney(total.monthly, cur!) : "—"}
              </p>
              <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                {costs.length} costo{costs.length === 1 ? "" : "s"} registrado
                {costs.length === 1 ? "" : "s"}
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="text-xs text-[var(--muted-foreground)]">
                Confirmado vs estimado
              </p>
              <div className="mt-2 flex flex-col gap-1">
                {byCertainty.length === 0 ? (
                  <span className="text-sm text-[var(--muted-foreground)]">—</span>
                ) : (
                  byCertainty.map((c) => (
                    <div
                      key={c.certainty}
                      className="tabular flex items-center justify-between text-sm"
                    >
                      <span className="text-[var(--muted-foreground)]">
                        {c.certainty}
                      </span>
                      <span className="font-medium">
                        {formatMoney(c.monthly, c.currency)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="mb-2 text-sm font-medium">Costo por categoría</p>
              {byCategory.length > 0 ? (
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <CategoryDonut
                      data={byCategory.map((c) => ({
                        label: c.label,
                        value: Number(c.monthly),
                      }))}
                      currency={cur ?? "USD"}
                    />
                  </div>
                  <ul className="flex flex-col gap-1.5 text-xs">
                    {byCategory.map((c, i) => (
                      <li key={c.label} className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{
                            background: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
                          }}
                        />
                        <span className="text-[var(--muted-foreground)]">
                          {c.label}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="py-12 text-center text-sm text-[var(--muted-foreground)]">
                  Sin categorías cargadas.
                </p>
              )}
            </div>

            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="mb-3 text-sm font-medium">Por proveedor</p>
              {byVendor.length === 0 ? (
                <p className="text-sm text-[var(--muted-foreground)]">Sin datos.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {byVendor.map((v) => (
                    <li
                      key={v.label}
                      className="tabular flex items-center justify-between text-sm"
                    >
                      <span className="text-[var(--muted-foreground)]">
                        {v.label}
                      </span>
                      <span className="font-medium">
                        {formatMoney(v.monthly, v.currency)}/mes
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {tab === "costs" ? (
        <div className="flex flex-col gap-4">
          <CreateCost
            workspaceId={workspaceId}
            applications={applications}
            vendors={vendors}
            lockApplicationId={application.id}
          />
          {costs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
              <p className="font-medium">Sin costos todavía</p>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                Agregá el primer costo de {application.name}.
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
        </div>
      ) : null}

      {tab === "environments" ? (
        <div className="flex flex-col gap-4">
          <CreateEnvironment workspaceId={workspaceId} applicationId={application.id} />
          {environments.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
              <p className="font-medium">Sin environments todavía</p>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                Agregá production, staging u otros environments de {application.name}.
              </p>
            </div>
          ) : (
            <ul className="flex flex-col gap-2">
              {environments.map((env) => (
                <li
                  key={env.id}
                  className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
                >
                  <div>
                    <p className="font-medium">{env.name}</p>
                    {env.url ? (
                      <p className="text-xs text-[var(--muted-foreground)]">
                        {env.url}
                      </p>
                    ) : null}
                  </div>
                  <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]">
                    {ENV_TYPE_LABEL[env.type] ?? env.type}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {tab === "history" ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="mb-3 text-sm font-medium">Cambios de costo recientes</p>
          {recentChanges.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)]">
              Todavía no hay cambios registrados para {application.name}.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {recentChanges.map((c) => (
                <li
                  key={`${c.cost_id}-${c.effective_from}-${c.amount}`}
                  className="tabular flex items-center justify-between text-sm"
                >
                  <div>
                    <span className="font-medium">{c.cost_name}</span>
                    <span className="ml-2 text-xs text-[var(--muted-foreground)]">
                      {c.reason ?? "actualización"} · {c.effective_from}
                    </span>
                  </div>
                  <span className="font-medium">
                    {formatMoney(c.amount, c.currency)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
