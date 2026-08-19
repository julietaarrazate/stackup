"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CreateWorkspace() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    const res = await fetch("/api/v1/workspaces", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo crear el workspace.");
      return;
    }
    setName("");
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
      <Input
        aria-label="Nombre del workspace"
        placeholder="Nombre del workspace (ej. Oído)"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Button type="submit" disabled={busy || !name.trim()} className="shrink-0">
        <Plus className="h-4 w-4" />
        {busy ? "Creando…" : "Crear"}
      </Button>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
