"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Paperclip, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Cost } from "@/lib/session";

const CURRENCIES = ["USD", "ARS", "EUR", "BRL", "MXN"];

export function RecordExpense({
  workspaceId,
  costs,
}: {
  workspaceId: string;
  costs: Cost[];
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}`;

  const [costId, setCostId] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [paidAt, setPaidAt] = useState("");
  const [invoice, setInvoice] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setDone(false);
    if (!costId || !amount) {
      setError("Elegí un costo y un monto.");
      return;
    }
    setBusy(true);

    let evidenceId: string | null = null;
    if (file) {
      const form = new FormData();
      form.set("file", file);
      form.set("type", "invoice");
      const up = await fetch(`${base}/evidence`, { method: "POST", body: form });
      if (!up.ok) {
        setBusy(false);
        setError("No se pudo subir el comprobante (tipo o tamaño no válido).");
        return;
      }
      evidenceId = (await up.json()).id as string;
    }

    const res = await fetch(`${base}/expenses`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        cost_item_id: costId,
        amount,
        currency,
        paid_at: paidAt || null,
        status: "paid",
        invoice_number: invoice.trim() || null,
        evidence_id: evidenceId,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo registrar el pago.");
      return;
    }
    setDone(true);
    setAmount("");
    setInvoice("");
    setFile(null);
    router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <p className="text-sm font-medium">Registrar un pago</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Costo" htmlFor="exp-cost">
          <Select
            id="exp-cost"
            value={costId}
            onChange={(e) => {
              setCostId(e.target.value);
              const c = costs.find((x) => x.id === e.target.value);
              if (c) setCurrency(c.currency);
            }}
          >
            <option value="">Elegí uno…</option>
            {costs.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Fecha de pago" htmlFor="exp-date">
          <Input
            id="exp-date"
            type="date"
            value={paidAt}
            onChange={(e) => setPaidAt(e.target.value)}
          />
        </Field>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Monto" htmlFor="exp-amount">
          <Input
            id="exp-amount"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </Field>
        <Field label="Moneda" htmlFor="exp-currency">
          <Select
            id="exp-currency"
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
        <Field label="N° factura (opc.)" htmlFor="exp-invoice">
          <Input
            id="exp-invoice"
            value={invoice}
            onChange={(e) => setInvoice(e.target.value)}
          />
        </Field>
      </div>
      <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-[var(--muted-foreground)]">
        <Paperclip className="h-4 w-4" />
        {file ? file.name : "Adjuntar comprobante (PDF o imagen, opcional)"}
        <input
          type="file"
          accept="application/pdf,image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      {done ? (
        <p className="text-sm text-[var(--positive)]">Pago registrado.</p>
      ) : null}
      <div>
        <Button type="submit" disabled={busy}>
          <Plus className="h-4 w-4" />
          {busy ? "Guardando…" : "Registrar pago"}
        </Button>
      </div>
    </form>
  );
}
