"use client";

import { useEffect, useState } from "react";
import { CategoryDonut, EvolutionArea, CATEGORY_COLORS } from "./dashboard-charts";
import { EntityIcon } from "./entity-icon";
import { formatMoney } from "@/lib/format";
import type { Application, EvolutionReport, OverviewReport } from "@/lib/session";

const PERIODS = [3, 6, 12, 24];

function primaryCurrency(overview: OverviewReport | null): string | null {
  if (!overview || overview.total.length === 0) return null;
  const sorted = [...overview.total].sort(
    (a, b) => Number(b.monthly) - Number(a.monthly),
  );
  return sorted[0]?.currency ?? null;
}

export function ReportsExplorer({
  workspaceId,
  applications,
  initialOverview,
  initialEvolution,
}: {
  workspaceId: string;
  applications: Application[];
  initialOverview: OverviewReport | null;
  initialEvolution: EvolutionReport;
}) {
  const base = `/api/v1/workspaces/${workspaceId}`;

  const [applicationId, setApplicationId] = useState("");
  const [category, setCategory] = useState("");
  const [months, setMonths] = useState(6);

  const [overview, setOverview] = useState(initialOverview);
  const [evolution, setEvolution] = useState(initialEvolution);

  useEffect(() => {
    let active = true;
    const qs = new URLSearchParams();
    if (applicationId) qs.set("application_id", applicationId);
    if (category.trim()) qs.set("category", category.trim());
    Promise.all([
      fetch(`${base}/reports/overview?${qs.toString()}`).then((r) =>
        r.ok ? r.json() : null,
      ),
      fetch(`${base}/reports/evolution?months=${months}`).then((r) =>
        r.ok ? r.json() : { points: [] },
      ),
    ]).then(([ov, evo]) => {
      if (!active) return;
      setOverview(ov);
      setEvolution(evo);
    });
    return () => {
      active = false;
    };
  }, [applicationId, category, months, base]);

  const cur = primaryCurrency(overview);
  const total = overview?.total.find((t) => t.currency === cur);
  const categories = (overview?.by_category ?? [])
    .filter((g) => g.currency === cur)
    .map((g) => ({ label: g.label, value: Number(g.monthly) }));
  const evoSeries = evolution.points
    .filter((p) => p.currency === cur)
    .map((p) => ({ period: p.period.slice(2), value: Number(p.monthly) }));

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="rep-app" className="text-xs font-medium">
            Aplicación
          </label>
          <select
            id="rep-app"
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm"
          >
            <option value="">Todas</option>
            {applications.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="rep-cat" className="text-xs font-medium">
            Categoría
          </label>
          <input
            id="rep-cat"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="infrastructure…"
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm placeholder:text-[var(--muted-foreground)]"
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium">Evolución</span>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setMonths(p)}
                className={`rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  months === p
                    ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                }`}
              >
                {p}m
              </button>
            ))}
          </div>
        </div>
      </div>

      {!overview || overview.cost_item_count === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Sin datos para estos filtros</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Ajustá los filtros o cargá costos primero.
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="text-xs text-[var(--muted-foreground)]">
                Costo mensual{cur ? ` (${cur})` : ""}
              </p>
              <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
                {total ? formatMoney(total.monthly, cur!) : "—"}
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="text-xs text-[var(--muted-foreground)]">Anualizado</p>
              <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
                {total ? formatMoney(total.annualized, cur!) : "—"}
              </p>
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="mb-2 text-sm font-medium">Evolución del costo mensual</p>
              {evoSeries.some((p) => p.value > 0) ? (
                <EvolutionArea data={evoSeries} currency={cur ?? "USD"} />
              ) : (
                <p className="py-16 text-center text-sm text-[var(--muted-foreground)]">
                  Sin datos suficientes todavía.
                </p>
              )}
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
              <p className="mb-2 text-sm font-medium">Costo por categoría</p>
              {categories.length > 0 ? (
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <CategoryDonut data={categories} currency={cur ?? "USD"} />
                  </div>
                  <ul className="flex flex-col gap-1.5 text-xs">
                    {categories.map((c, i) => (
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
                <p className="py-16 text-center text-sm text-[var(--muted-foreground)]">
                  Sin categorías cargadas.
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <ReportGroup
              title="Por aplicación"
              rows={(overview.by_application ?? []).filter((g) => g.currency === cur)}
              currency={cur ?? "USD"}
            />
            <ReportGroup
              title="Por proveedor"
              rows={(overview.by_vendor ?? []).filter((g) => g.currency === cur)}
              currency={cur ?? "USD"}
            />
          </div>
        </>
      )}
    </div>
  );
}

function ReportGroup({
  title,
  rows,
  currency,
}: {
  title: string;
  rows: { label: string; monthly: string }[];
  currency: string;
}) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <p className="mb-3 text-sm font-medium">{title}</p>
      {rows.length === 0 ? (
        <p className="text-sm text-[var(--muted-foreground)]">Sin datos.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {rows.map((r) => (
            <li
              key={r.label}
              className="tabular flex items-center justify-between gap-2 text-sm"
            >
              <span className="flex min-w-0 items-center gap-2.5">
                <EntityIcon name={r.label} size="sm" />
                <span className="truncate text-[var(--muted-foreground)]">
                  {r.label}
                </span>
              </span>
              <span className="shrink-0 font-medium">
                {formatMoney(r.monthly, currency)}/mes
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
