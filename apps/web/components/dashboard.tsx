import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { EvolutionReport, OverviewReport } from "@/lib/session";
import { formatMoney } from "@/lib/format";
import { CategoryDonut, EvolutionArea, CATEGORY_COLORS } from "./dashboard-charts";

function primaryCurrency(overview: OverviewReport, base: string): string | null {
  if (overview.total.length === 0) return null;
  const hasBase = overview.total.find((t) => t.currency === base);
  if (hasBase) return base;
  const sorted = [...overview.total].sort(
    (a, b) => Number(b.monthly) - Number(a.monthly),
  );
  return sorted[0]?.currency ?? null;
}

const CERTAINTY_LABEL: Record<string, string> = {
  confirmed: "Confirmado",
  estimated: "Estimado",
  projected: "Proyectado",
};

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
  const otherCurrencies = overview.total.filter((t) => t.currency !== cur);

  return (
    <div className="flex flex-col gap-4">
      {/* KPI row */}
      <div className="grid gap-3 sm:grid-cols-3">
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
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">Anualizado</p>
          <p className="tabular mt-1 text-3xl font-semibold tracking-tight">
            {formatMoney(total.annualized, cur)}
          </p>
          <p className="mt-2 text-xs text-[var(--muted-foreground)]">
            {overview.cost_item_count} costos registrados
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted-foreground)]">
            Confirmado vs estimado
          </p>
          <div className="mt-2 flex flex-col gap-1">
            {certainty.length === 0 ? (
              <span className="text-sm text-[var(--muted-foreground)]">—</span>
            ) : (
              certainty.map((c) => (
                <div
                  key={c.certainty}
                  className="tabular flex items-center justify-between text-sm"
                >
                  <span className="text-[var(--muted-foreground)]">
                    {CERTAINTY_LABEL[c.certainty] ?? c.certainty}
                  </span>
                  <span className="font-medium">
                    {formatMoney(c.monthly, cur)}
                  </span>
                </div>
              ))
            )}
          </div>
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
                <div>
                  <span className="font-medium">{c.cost_name}</span>
                  <span className="ml-2 text-xs text-[var(--muted-foreground)]">
                    {c.reason ?? "actualización"} · {c.effective_from}
                  </span>
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
              className="tabular flex items-center justify-between text-sm"
            >
              <span className="text-[var(--muted-foreground)]">{r.label}</span>
              <span className="font-medium">
                {formatMoney(r.monthly, currency)}/mes
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
