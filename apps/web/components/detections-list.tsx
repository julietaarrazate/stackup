"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EntityIcon } from "@/components/entity-icon";
import type { Application, Detection, Vendor } from "@/lib/session";

type Service = { id: string; name: string };

const CURRENCIES = ["USD", "ARS", "EUR", "BRL", "MXN"];
const FREQUENCIES = [
  ["monthly", "Mensual"],
  ["yearly", "Anual"],
  ["quarterly", "Trimestral"],
  ["weekly", "Semanal"],
] as const;

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "Alta confianza",
  medium: "Confianza media",
};

export function DetectionsList({
  workspaceId,
  detections,
  applications,
  vendors,
}: {
  workspaceId: string;
  detections: Detection[];
  applications: Application[];
  vendors: Vendor[];
}) {
  const router = useRouter();
  const [expanded, setExpanded] = useState<string | null>(null);

  async function dismiss(id: string) {
    const res = await fetch(
      `/api/v1/workspaces/${workspaceId}/detections/${id}/dismiss`,
      { method: "POST" },
    );
    if (res.ok) router.refresh();
  }

  if (detections.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
        <p className="font-medium">Sin detecciones pendientes</p>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Escaneá un repositorio conectado para encontrar proveedores que ya
          estás pagando.
        </p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {detections.map((d) => (
        <li
          key={d.id}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)]"
        >
          <div className="flex items-center justify-between gap-3 px-4 py-3.5">
            <div className="flex min-w-0 items-center gap-3">
              <EntityIcon name={d.vendor_name} />
              <div className="min-w-0">
                <p className="truncate font-medium">{d.vendor_name}</p>
                <p className="truncate text-xs text-[var(--muted-foreground)]">
                  {d.evidence} · {CONFIDENCE_LABEL[d.confidence] ?? d.confidence}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button
                variant="ghost"
                onClick={() => setExpanded(expanded === d.id ? null : d.id)}
              >
                <Check className="h-4 w-4" />
                Confirmar
              </Button>
              <button
                type="button"
                onClick={() => dismiss(d.id)}
                aria-label={`Descartar ${d.vendor_name}`}
                className="rounded-lg p-2 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          {expanded === d.id ? (
            <div className="border-t border-[var(--border)] px-4 py-4">
              <ConfirmForm
                workspaceId={workspaceId}
                detection={d}
                applications={applications}
                vendors={vendors}
                onDone={() => {
                  setExpanded(null);
                  router.refresh();
                }}
              />
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

function ConfirmForm({
  workspaceId,
  detection,
  applications,
  vendors,
  onDone,
}: {
  workspaceId: string;
  detection: Detection;
  applications: Application[];
  vendors: Vendor[];
  onDone: () => void;
}) {
  const base = `/api/v1/workspaces/${workspaceId}`;

  const [applicationId, setApplicationId] = useState(detection.application_id ?? "");
  const [vendorId, setVendorId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [services, setServices] = useState<Service[]>([]);
  const [name, setName] = useState(detection.vendor_name);
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [frequency, setFrequency] = useState("monthly");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!vendorId) return;
    let active = true;
    fetch(`${base}/vendors/${vendorId}/services`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => active && setServices(data))
      .catch(() => active && setServices([]));
    return () => {
      active = false;
    };
  }, [vendorId, base]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!applicationId || !serviceId || !amount) {
      setError("Completá aplicación, servicio y monto.");
      return;
    }
    setBusy(true);
    setError(null);
    const res = await fetch(`${base}/detections/${detection.id}/confirm`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        application_id: applicationId,
        service_id: serviceId,
        name: name.trim() || detection.vendor_name,
        category: detection.category,
        amount,
        currency,
        frequency,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo confirmar. Revisá los datos.");
      return;
    }
    onDone();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Aplicación" htmlFor="det-app">
          <Select
            id="det-app"
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
          >
            <option value="">Elegí una…</option>
            {applications.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Nombre del costo" htmlFor="det-name">
          <Input id="det-name" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Proveedor" htmlFor="det-vendor">
          <Select
            id="det-vendor"
            value={vendorId}
            onChange={(e) => {
              setVendorId(e.target.value);
              setServiceId("");
              setServices([]);
            }}
          >
            <option value="">Elegí uno…</option>
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Servicio" htmlFor="det-service">
          <Select
            id="det-service"
            value={serviceId}
            onChange={(e) => setServiceId(e.target.value)}
            disabled={!vendorId}
          >
            <option value="">Elegí uno…</option>
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Monto" htmlFor="det-amount">
          <Input
            id="det-amount"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </Field>
        <Field label="Moneda" htmlFor="det-currency">
          <Select
            id="det-currency"
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
        <Field label="Frecuencia" htmlFor="det-frequency">
          <Select
            id="det-frequency"
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
          >
            {FREQUENCIES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      <div>
        <Button type="submit" disabled={busy}>
          {busy ? "Guardando…" : "Crear costo"}
        </Button>
      </div>
    </form>
  );
}
