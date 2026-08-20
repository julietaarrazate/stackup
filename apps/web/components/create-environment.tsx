"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

const TYPES = [
  ["production", "Producción"],
  ["staging", "Staging"],
  ["development", "Desarrollo"],
  ["preview", "Preview"],
  ["other", "Otro"],
] as const;

export function CreateEnvironment({
  workspaceId,
  applicationId,
}: {
  workspaceId: string;
  applicationId: string;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [type, setType] = useState<string>("production");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    const res = await fetch(
      `/api/v1/workspaces/${workspaceId}/applications/${applicationId}/environments`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: name.trim(), type }),
      },
    );
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo crear el environment.");
      return;
    }
    setName("");
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
      <Input
        aria-label="Nombre del environment"
        placeholder="Nombre (ej. production)"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Select
        aria-label="Tipo de environment"
        value={type}
        onChange={(e) => setType(e.target.value)}
        className="sm:w-44"
      >
        {TYPES.map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </Select>
      <Button type="submit" disabled={busy || !name.trim()} className="shrink-0">
        <Plus className="h-4 w-4" />
        {busy ? "Creando…" : "Agregar"}
      </Button>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
