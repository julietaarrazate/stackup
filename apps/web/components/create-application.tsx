"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CreateApplication({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [repo, setRepo] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/v1/workspaces/${workspaceId}/applications`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        repository_url: repo.trim() || null,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo crear la aplicación.");
      return;
    }
    setName("");
    setRepo("");
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          aria-label="Nombre de la aplicación"
          placeholder="Nombre (ej. Oído)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          aria-label="URL del repositorio"
          placeholder="Repositorio (opcional)"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
        />
        <Button type="submit" disabled={busy || !name.trim()} className="shrink-0">
          <Plus className="h-4 w-4" />
          {busy ? "Creando…" : "Agregar"}
        </Button>
      </div>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
