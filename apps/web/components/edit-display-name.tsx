"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function EditDisplayName({
  fullName,
  email,
}: {
  fullName: string | null;
  email: string;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(fullName ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const res = await fetch("/api/v1/users/me", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ full_name: name.trim() || null }),
    });
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo guardar el nombre.");
      return;
    }
    setEditing(false);
    router.refresh();
  }

  if (!editing) {
    return (
      <div className="flex items-center gap-2">
        <div>
          <p className="text-sm text-[var(--muted-foreground)]">Sesión iniciada como</p>
          <p className="font-medium">{fullName || email}</p>
          {fullName ? (
            <p className="text-xs text-[var(--muted-foreground)]">{email}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => setEditing(true)}
          aria-label="Editar nombre"
          className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--foreground)]"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <p className="text-sm text-[var(--muted-foreground)]">
        ¿Cómo querés que te llamemos?
      </p>
      <div className="flex items-center gap-2">
        <Input
          autoFocus
          placeholder={email}
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={160}
        />
        <Button type="submit" disabled={busy}>
          {busy ? "Guardando…" : "Guardar"}
        </Button>
        <Button type="button" variant="ghost" onClick={() => setEditing(false)}>
          Cancelar
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
