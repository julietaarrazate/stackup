"use client";

import { Fragment, useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { formatMoney } from "@/lib/format";
import type { Cost } from "@/lib/session";

const FREQUENCY_LABEL: Record<string, string> = {
  weekly: "semanal",
  monthly: "mensual",
  quarterly: "trimestral",
  yearly: "anual",
  custom: "custom",
};

const CURRENCIES = ["USD", "ARS", "EUR", "BRL", "MXN"];
const FREQUENCIES = [
  ["monthly", "Mensual"],
  ["yearly", "Anual"],
  ["quarterly", "Trimestral"],
  ["weekly", "Semanal"],
] as const;
const STATUSES = [
  ["active", "Activo"],
  ["paused", "Pausado"],
  ["ended", "Finalizado"],
] as const;

export function CostsList({
  workspaceId,
  costs,
  appName,
}: {
  workspaceId: string;
  costs: Cost[];
  appName: Map<string, string>;
}) {
  const router = useRouter();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function remove(cost: Cost) {
    if (
      !window.confirm(
        `¿Eliminar "${cost.name}"? Esto lo marca como finalizado y deja de contarlo en los reportes.`,
      )
    ) {
      return;
    }
    setBusyId(cost.id);
    const res = await fetch(`/api/v1/workspaces/${workspaceId}/costs/${cost.id}`, {
      method: "DELETE",
    });
    setBusyId(null);
    if (res.ok) router.refresh();
  }

  return (
    <>
      {/* Mobile: card list */}
      <ul className="flex flex-col gap-2 lg:hidden">
        {costs.map((c) => (
          <li
            key={c.id}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)]"
          >
            <div className="tabular flex items-center justify-between px-4 py-3">
              <div className="min-w-0">
                <p className="truncate font-medium">{c.name}</p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {appName.get(c.application_id) ?? "—"} ·{" "}
                  {formatMoney(c.amount, c.currency)} ·{" "}
                  {FREQUENCY_LABEL[c.frequency] ?? c.frequency}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <div className="text-right">
                  <p className="font-semibold">
                    {formatMoney(c.monthly_equivalent, c.currency)}/mes
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {formatMoney(c.annualized_cost, c.currency)} anual
                  </p>
                </div>
                <RowActions
                  editing={editingId === c.id}
                  busy={busyId === c.id}
                  onEdit={() => setEditingId(editingId === c.id ? null : c.id)}
                  onDelete={() => remove(c)}
                />
              </div>
            </div>
            {editingId === c.id ? (
              <div className="border-t border-[var(--border)] px-4 py-3">
                <EditCostForm
                  workspaceId={workspaceId}
                  cost={c}
                  onDone={() => {
                    setEditingId(null);
                    router.refresh();
                  }}
                />
              </div>
            ) : null}
          </li>
        ))}
      </ul>

      {/* Desktop: table */}
      <div className="hidden overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface)] lg:block">
        <table className="tabular w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs text-[var(--muted-foreground)]">
              <th className="px-4 py-3 font-medium">Costo</th>
              <th className="px-4 py-3 font-medium">Aplicación</th>
              <th className="px-4 py-3 font-medium">Categoría</th>
              <th className="px-4 py-3 font-medium">Frecuencia</th>
              <th className="px-4 py-3 text-right font-medium">Monto</th>
              <th className="px-4 py-3 text-right font-medium">Mensual</th>
              <th className="px-4 py-3 text-right font-medium">Anual</th>
              <th className="px-4 py-3 text-right font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {costs.map((c) => (
              <Fragment key={c.id}>
                <tr className="border-b border-[var(--border)] last:border-0">
                  <td className="px-4 py-3">
                    <p className="font-medium">{c.name}</p>
                    {c.certainty !== "confirmed" || c.status !== "active" ? (
                      <p className="text-xs text-[var(--muted-foreground)]">
                        {c.certainty !== "confirmed" ? c.certainty : ""}
                        {c.certainty !== "confirmed" && c.status !== "active"
                          ? " · "
                          : ""}
                        {c.status !== "active" ? c.status : ""}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-[var(--muted-foreground)]">
                    {appName.get(c.application_id) ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-[var(--muted-foreground)]">
                    {c.category ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-[var(--muted-foreground)]">
                    {FREQUENCY_LABEL[c.frequency] ?? c.frequency}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {formatMoney(c.amount, c.currency)}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold">
                    {formatMoney(c.monthly_equivalent, c.currency)}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--muted-foreground)]">
                    {formatMoney(c.annualized_cost, c.currency)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <RowActions
                        editing={editingId === c.id}
                        busy={busyId === c.id}
                        onEdit={() => setEditingId(editingId === c.id ? null : c.id)}
                        onDelete={() => remove(c)}
                      />
                    </div>
                  </td>
                </tr>
                {editingId === c.id ? (
                  <tr className="border-b border-[var(--border)]">
                    <td colSpan={8} className="bg-[var(--surface-2)] px-4 py-4">
                      <EditCostForm
                        workspaceId={workspaceId}
                        cost={c}
                        onDone={() => {
                          setEditingId(null);
                          router.refresh();
                        }}
                      />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function RowActions({
  editing,
  busy,
  onEdit,
  onDelete,
}: {
  editing: boolean;
  busy: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={onEdit}
        aria-label="Editar costo"
        aria-pressed={editing}
        className={`rounded-lg p-1.5 hover:bg-[var(--surface-2)] ${
          editing
            ? "text-[var(--primary)]"
            : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        }`}
      >
        <Pencil className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={onDelete}
        disabled={busy}
        aria-label="Eliminar costo"
        className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)] disabled:opacity-50"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}

function EditCostForm({
  workspaceId,
  cost,
  onDone,
}: {
  workspaceId: string;
  cost: Cost;
  onDone: () => void;
}) {
  const [name, setName] = useState(cost.name);
  const [amount, setAmount] = useState(cost.amount);
  const [currency, setCurrency] = useState(cost.currency);
  const [frequency, setFrequency] = useState(cost.frequency);
  const [category, setCategory] = useState(cost.category ?? "");
  const [status, setStatus] = useState(cost.status);
  const [changeReason, setChangeReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/v1/workspaces/${workspaceId}/costs/${cost.id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        amount,
        currency,
        frequency,
        category: category.trim() || null,
        status,
        change_reason: changeReason.trim() || null,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo guardar. Revisá los datos.");
      return;
    }
    onDone();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Nombre" htmlFor={`edit-name-${cost.id}`}>
          <Input
            id={`edit-name-${cost.id}`}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <Field label="Monto" htmlFor={`edit-amount-${cost.id}`}>
          <Input
            id={`edit-amount-${cost.id}`}
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </Field>
        <Field label="Moneda" htmlFor={`edit-currency-${cost.id}`}>
          <Select
            id={`edit-currency-${cost.id}`}
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Frecuencia" htmlFor={`edit-freq-${cost.id}`}>
          <Select
            id={`edit-freq-${cost.id}`}
            value={frequency}
            onChange={(e) => setFrequency(e.target.value as typeof frequency)}
          >
            {FREQUENCIES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Categoría" htmlFor={`edit-category-${cost.id}`}>
          <Input
            id={`edit-category-${cost.id}`}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </Field>
        <Field label="Estado" htmlFor={`edit-status-${cost.id}`}>
          <Select
            id={`edit-status-${cost.id}`}
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            {STATUSES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <Field label="Motivo del cambio (opcional)" htmlFor={`edit-reason-${cost.id}`}>
        <Input
          id={`edit-reason-${cost.id}`}
          placeholder="ej. Cambio de plan"
          value={changeReason}
          onChange={(e) => setChangeReason(e.target.value)}
        />
      </Field>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      <div>
        <Button type="submit" disabled={busy}>
          {busy ? "Guardando…" : "Guardar cambios"}
        </Button>
      </div>
    </form>
  );
}
