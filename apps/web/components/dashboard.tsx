import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { EvolutionReport, OverviewReport } from "@/lib/session";
import { formatMoney } from "@/lib/format";
import {
  CategoryDonut,
  EvolutionArea,
  Sparkline,
  CATEGORY_COLORS,
} from "./dashboard-charts";
import { EntityIcon } from "./entity-icon";

function primaryCurrency(overview: OverviewReport, base: string): string | null {
  if (overview.total.length === 0) return null;
  const hasBase = overview.total.find((t) => t.currency === base);
  if (hasBase) return base;
  const sorted = [...overview.total].sort(
    (a, b) => Number(b.monthly) - Number(a.monthly),
  );
  return sorted[0]?.currency ?? null;
}

export function Dashboard({
  overview,
  evolution,
  baseCurrency,
}: {
  overview: OverviewReport;
  evolution: EvolutionReport;
  baseCurrency: string;
}) {
  const cur = primaryCurrency(overview, baseCurrency);
  if (!cur) return null;

  const total = overview.total.find((t) => t.currency === cur)!;
  const categories = overview.by_category
    .filter((g) => g.currency === cur)
    .map((g) => ({ label: g.label, value: Number(g.monthly) }));
  const evoSeries = evolution.points
    .filter((p) => p.currency === cur)
    .map((p) => ({ period: p.period.slice(2), value: Number(p.monthly) }));

  // Change vs previous month (primary currency).
  let change: number | null = null;
  const prev = evoSeries[evoSeries.length - 2];
  const last = evoSeries[evoSeries.length - 1];
  if (prev && last && prev.value > 0) {
    change = ((last.value - prev.value) / prev.value) * 100;
  }

  const certainty = overview.by_certainty.filter((c) => c.currency === cur);
  const confirmed = certainty.find((c) => c.certainty === "confirmed");
  const estimated = certainty.find((c) => c.certainty === "estimated");
  const totalMonthly = Number(total.monthly) || 0;
  const confirmedPct = totalMonthly
    ? (Number(confirmed?.monthly ?? 0) / totalMonthly) * 100
    : 0;
  const estimatedPct = totalMonthly
    ? (Number(estimated?.monthly ?? 0) / totalMonthly) * 100
    : 0;
  const otherCurrencies = overview.total.filter((t) => t.currency !== cur);
  const sparkValues = evoSeries.map((p) => p.value);

  return (
    <div className="flex flex-col gap-4">
      {/* KPI row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">
            Costo mensual total ({cur})
          </p>
          <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
            {formatMoney(total.monthly, cur)}
          </p>
          {change !== null ? (
            <p
              className={`tabular mt-2 inline-flex items-center gap-1 text-xs ${
                change >= 0 ? "text-[var(--negative)]" : "text-[var(--positive)]"
              }`}
            >
              {change >= 0 ? (
                <ArrowUpRight className="h-3.5 w-3.5" />
              ) : (
                <ArrowDownRight className="h-3.5 w-3.5" />
              )}
              {Math.abs(change).toFixed(1)}% vs mes anterior
            </p>
          ) : null}
          <Sparkline data={sparkValues} color="#8b5cf6" />
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">Anualizado</p>
          <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
            {formatMoney(total.annualized, cur)}
          </p>
          <p className="mt-2 text-xs text-[var(--muted-foreground)]">
            {overview.cost_item_count} costos registrados
          </p>
          <Sparkline data={sparkValues.map((v) => v * 12)} color="#22b8cf" />
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">Confirmado</p>
          <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
            {formatMoney(confirmed?.monthly ?? "0", cur)}
          </p>
          <p className="tabular mt-2 text-xs text-[var(--positive)]">
            {confirmedPct.toFixed(1)}% del total
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">Estimado</p>
          <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
            {formatMoney(estimated?.monthly ?? "0", cur)}
          </p>
          <p className="tabular mt-2 text-xs text-[var(--muted-foreground)]">
            {estimatedPct.toFixed(1)}% del total
          </p>
        </div>
      </div>

      {otherCurrencies.length > 0 ? (
        <div className="tabular flex flex-wrap gap-3 text-sm text-[var(--muted-foreground)]">
          {otherCurrencies.map((t) => (
            <span
              key={t.currency}
              className="rounded-lg border border-[var(--border)] px-3 py-1"
            >
              {formatMoney(t.monthly, t.currency)}/mes ({t.currency})
            </span>
          ))}
        </div>
      ) : null}

      {/* Charts */}
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="mb-2 text-sm font-medium">Evolución del costo mensual</p>
          {evoSeries.some((p) => p.value > 0) ? (
            <EvolutionArea data={evoSeries} currency={cur} />
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
                <CategoryDonut data={categories} currency={cur} />
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

      {/* By application / vendor + recent changes */}
      <div className="grid gap-3 lg:grid-cols-2">
        <GroupList
          title="Por aplicación"
          rows={overview.by_application.filter((g) => g.currency === cur)}
          currency={cur}
        />
        <GroupList
          title="Por proveedor"
          rows={overview.by_vendor.filter((g) => g.currency === cur)}
          currency={cur}
        />
      </div>

      {overview.recent_changes.length > 0 ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="mb-3 text-sm font-medium">Cambios recientes</p>
          <ul className="flex flex-col gap-2">
            {overview.recent_changes.map((c) => (
              <li
                key={`${c.cost_id}-${c.effective_from}-${c.amount}`}
                className="tabular flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-2.5">
                  <EntityIcon name={c.cost_name} size="sm" />
                  <div>
                    <span className="font-medium">{c.cost_name}</span>
                    <span className="ml-2 text-xs text-[var(--muted-foreground)]">
                      {c.reason ?? "actualización"} · {c.effective_from}
                    </span>
                  </div>
                </div>
                <span>{formatMoney(c.amount, c.currency)}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function GroupList({
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
