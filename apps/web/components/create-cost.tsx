"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { formatMoney } from "@/lib/format";
import type { Application } from "@/lib/session";

type Vendor = { id: string; name: string; is_global: boolean };
type Service = { id: string; name: string };
type Environment = { id: string; name: string };

const CURRENCIES = ["USD", "ARS", "EUR", "BRL", "MXN"];
const FREQUENCIES = [
  ["monthly", "Mensual"],
  ["yearly", "Anual"],
  ["quarterly", "Trimestral"],
  ["weekly", "Semanal"],
  ["one_time", "Único"],
] as const;

type Saved = { monthly_equivalent: string; annualized_cost: string; currency: string };

export function CreateCost({
  workspaceId,
  applications,
  vendors,
  lockApplicationId,
}: {
  workspaceId: string;
  applications: Application[];
  vendors: Vendor[];
  /** When set, the application is fixed (no selector shown) — used from an
   * application's own detail page, where it would be redundant to re-pick it. */
  lockApplicationId?: string;
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}`;

  const [applicationId, setApplicationId] = useState(lockApplicationId ?? "");
  const [vendorId, setVendorId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [services, setServices] = useState<Service[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);

  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [frequency, setFrequency] = useState<string>("monthly");
  const [category, setCategory] = useState("");
  const [certainty, setCertainty] = useState("confirmed");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<Saved | null>(null);

  // Load a vendor's services when it changes (resets happen in onChange).
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

  // Load an application's environments when it changes.
  useEffect(() => {
    if (!applicationId) return;
    let active = true;
    fetch(`${base}/applications/${applicationId}/environments`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => active && setEnvironments(data))
      .catch(() => active && setEnvironments([]));
    return () => {
      active = false;
    };
  }, [applicationId, base]);

  function onVendorChange(id: string) {
    setVendorId(id);
    setServiceId("");
    setServices([]);
  }

  function onApplicationChange(id: string) {
    setApplicationId(id);
    setEnvironmentId("");
    setEnvironments([]);
  }

  const isOneTime = frequency === "one_time";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(null);
    if (!applicationId || !serviceId || !name.trim() || !amount) {
      setError("Completá aplicación, servicio, nombre y monto.");
      return;
    }
    setBusy(true);
    const res = await fetch(`${base}/costs`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        application_id: applicationId,
        service_id: serviceId,
        environment_id: environmentId || null,
        name: name.trim(),
        category: category.trim() || null,
        billing_type: isOneTime ? "one_time" : "fixed",
        amount,
        currency,
        frequency: isOneTime ? "monthly" : frequency,
        certainty,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo guardar el costo. Revisá los datos.");
      return;
    }
    const cost = (await res.json()) as Saved;
    setSaved(cost);
    setName("");
    setAmount("");
    setCategory("");
    router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <p className="text-sm font-medium">¿Qué estás pagando?</p>

      <div className="grid gap-3 sm:grid-cols-2">
        {lockApplicationId ? null : (
          <Field label="Aplicación" htmlFor="cost-app">
            <Select
              id="cost-app"
              value={applicationId}
              onChange={(e) => onApplicationChange(e.target.value)}
            >
              <option value="">Elegí una…</option>
              {applications.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </Select>
          </Field>
        )}

        <Field label="Environment (opcional)" htmlFor="cost-env">
          <Select
            id="cost-env"
            value={environmentId}
            onChange={(e) => setEnvironmentId(e.target.value)}
            disabled={!applicationId}
          >
            <option value="">—</option>
            {environments.map((env) => (
              <option key={env.id} value={env.id}>
                {env.name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Vendor" htmlFor="cost-vendor">
          <Select
            id="cost-vendor"
            value={vendorId}
            onChange={(e) => onVendorChange(e.target.value)}
          >
            <option value="">Elegí uno…</option>
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Servicio" htmlFor="cost-service">
          <Select
            id="cost-service"
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

      <Field label="Nombre del costo" htmlFor="cost-name">
        <Input
          id="cost-name"
          placeholder="ej. Vercel Pro"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </Field>

      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Monto" htmlFor="cost-amount">
          <Input
            id="cost-amount"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            placeholder="20.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </Field>
        <Field label="Moneda" htmlFor="cost-currency">
          <Select
            id="cost-currency"
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
        <Field label="Frecuencia" htmlFor="cost-frequency">
          <Select
            id="cost-frequency"
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

      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Categoría (opcional)" htmlFor="cost-category">
          <Input
            id="cost-category"
            placeholder="infrastructure, software, apis…"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </Field>
        <Field label="Certeza" htmlFor="cost-certainty">
          <Select
            id="cost-certainty"
            value={certainty}
            onChange={(e) => setCertainty(e.target.value)}
          >
            <option value="confirmed">Confirmado</option>
            <option value="estimated">Estimado</option>
            <option value="projected">Proyectado</option>
          </Select>
        </Field>
      </div>

      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}

      {saved ? (
        <div className="tabular rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-sm">
          Guardado ·{" "}
          <span className="font-medium text-[var(--foreground)]">
            {formatMoney(saved.monthly_equivalent, saved.currency)}/mes
          </span>{" "}
          · {formatMoney(saved.annualized_cost, saved.currency)} anual
        </div>
      ) : null}

      <div>
        <Button type="submit" disabled={busy}>
          <Plus className="h-4 w-4" />
          {busy ? "Guardando…" : "Agregar costo"}
        </Button>
      </div>
    </form>
  );
}
