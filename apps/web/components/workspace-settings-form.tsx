"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Workspace } from "@/lib/session";

const CURRENCIES = ["USD", "ARS", "EUR", "BRL", "MXN"];

export function WorkspaceSettingsForm({ workspace }: { workspace: Workspace }) {
  const router = useRouter();
  const [name, setName] = useState(workspace.name);
  const [currency, setCurrency] = useState(workspace.base_currency);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(false);
    const res = await fetch(`/api/v1/workspaces/${workspace.id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: name.trim(), base_currency: currency }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo guardar. Revisá los permisos y los datos.");
      return;
    }
    setSaved(true);
    router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <p className="text-sm font-medium">Workspace</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Nombre" htmlFor="ws-name">
          <Input id="ws-name" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Moneda base" htmlFor="ws-currency">
          <Select
            id="ws-currency"
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
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      {saved ? <p className="text-sm text-[var(--positive)]">Guardado.</p> : null}
      <div>
        <Button type="submit" disabled={busy || !name.trim()}>
          {busy ? "Guardando…" : "Guardar cambios"}
        </Button>
      </div>
    </form>
  );
}
