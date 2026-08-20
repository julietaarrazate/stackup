"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Application } from "@/lib/session";

export function ApplicationHeaderActions({
  workspaceId,
  application,
}: {
  workspaceId: string;
  application: Application;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  async function remove() {
    if (
      !window.confirm(
        `¿Eliminar "${application.name}"? Esto borra también sus environments y todos sus costos. No se puede deshacer.`,
      )
    ) {
      return;
    }
    setBusy(true);
    const res = await fetch(
      `/api/v1/workspaces/${workspaceId}/applications/${application.id}`,
      { method: "DELETE" },
    );
    setBusy(false);
    if (res.ok) router.push(`/app/${workspaceId}/applications`);
  }

  return (
    <>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => setEditing((v) => !v)}
          aria-label="Editar aplicación"
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
          onClick={remove}
          disabled={busy}
          aria-label="Eliminar aplicación"
          className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)] disabled:opacity-50"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
      {editing ? (
        <EditApplicationForm
          workspaceId={workspaceId}
          application={application}
          onDone={() => {
            setEditing(false);
            router.refresh();
          }}
        />
      ) : null}
    </>
  );
}

function EditApplicationForm({
  workspaceId,
  application,
  onDone,
}: {
  workspaceId: string;
  application: Application;
  onDone: () => void;
}) {
  const [name, setName] = useState(application.name);
  const [description, setDescription] = useState(application.description ?? "");
  const [repositoryUrl, setRepositoryUrl] = useState(application.repository_url ?? "");
  const [status, setStatus] = useState(application.status);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    const res = await fetch(
      `/api/v1/workspaces/${workspaceId}/applications/${application.id}`,
      {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          repository_url: repositoryUrl.trim() || null,
          status,
        }),
      },
    );
    setBusy(false);
    if (!res.ok) {
      setError("No se pudo guardar. Revisá los datos.");
      return;
    }
    onDone();
  }

  return (
    <form
      onSubmit={submit}
      className="mt-3 flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Nombre" htmlFor="app-edit-name">
          <Input
            id="app-edit-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <Field label="Estado" htmlFor="app-edit-status">
          <Select
            id="app-edit-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <option value="active">Activa</option>
            <option value="archived">Archivada</option>
          </Select>
        </Field>
      </div>
      <Field label="Descripción" htmlFor="app-edit-description">
        <Input
          id="app-edit-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </Field>
      <Field label="Repositorio" htmlFor="app-edit-repo">
        <Input
          id="app-edit-repo"
          value={repositoryUrl}
          onChange={(e) => setRepositoryUrl(e.target.value)}
        />
      </Field>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      <div>
        <Button type="submit" disabled={busy || !name.trim()}>
          {busy ? "Guardando…" : "Guardar cambios"}
        </Button>
      </div>
    </form>
  );
}
