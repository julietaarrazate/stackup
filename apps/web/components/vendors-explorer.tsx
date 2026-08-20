"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { EntityIcon } from "@/components/entity-icon";
import type { Service, Vendor } from "@/lib/session";

export function VendorsExplorer({
  workspaceId,
  vendors,
}: {
  workspaceId: string;
  vendors: Vendor[];
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}/vendors`;

  const [expanded, setExpanded] = useState<string | null>(null);
  const [services, setServices] = useState<Record<string, Service[]>>({});

  const [vendorName, setVendorName] = useState("");
  const [vendorBusy, setVendorBusy] = useState(false);
  const [vendorError, setVendorError] = useState<string | null>(null);

  async function toggle(vendorId: string) {
    if (expanded === vendorId) {
      setExpanded(null);
      return;
    }
    setExpanded(vendorId);
    if (!services[vendorId]) {
      const res = await fetch(`${base}/${vendorId}/services`);
      const data = res.ok ? ((await res.json()) as Service[]) : [];
      setServices((prev) => ({ ...prev, [vendorId]: data }));
    }
  }

  async function addVendor(e: React.FormEvent) {
    e.preventDefault();
    if (!vendorName.trim()) return;
    setVendorBusy(true);
    setVendorError(null);
    const res = await fetch(base, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: vendorName.trim() }),
    });
    setVendorBusy(false);
    if (!res.ok) {
      setVendorError("No se pudo crear el proveedor.");
      return;
    }
    setVendorName("");
    router.refresh();
  }

  async function removeVendor(vendorId: string) {
    const res = await fetch(`${base}/${vendorId}`, { method: "DELETE" });
    if (res.ok) router.refresh();
  }

  async function addService(vendorId: string, name: string) {
    if (!name.trim()) return;
    const res = await fetch(`${base}/${vendorId}/services`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
    if (!res.ok) return;
    const service = (await res.json()) as Service;
    setServices((prev) => ({
      ...prev,
      [vendorId]: [...(prev[vendorId] ?? []), service],
    }));
  }

  async function removeService(vendorId: string, serviceId: string) {
    const res = await fetch(`${base}/${vendorId}/services/${serviceId}`, {
      method: "DELETE",
    });
    if (!res.ok) return;
    setServices((prev) => ({
      ...prev,
      [vendorId]: (prev[vendorId] ?? []).filter((s) => s.id !== serviceId),
    }));
  }

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={addVendor}
        className="flex flex-col gap-2 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:flex-row sm:items-end"
      >
        <div className="flex-1">
          <Field label="Nuevo proveedor" htmlFor="vendor-name">
            <Input
              id="vendor-name"
              placeholder="ej. Cloudinary"
              value={vendorName}
              onChange={(e) => setVendorName(e.target.value)}
            />
          </Field>
        </div>
        <Button type="submit" disabled={vendorBusy || !vendorName.trim()}>
          <Plus className="h-4 w-4" />
          {vendorBusy ? "Creando…" : "Agregar"}
        </Button>
        {vendorError ? (
          <p className="text-sm text-[var(--negative)]" role="alert">
            {vendorError}
          </p>
        ) : null}
      </form>

      {vendors.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-10 text-center">
          <p className="font-medium">Sin proveedores todavía</p>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {vendors.map((v) => (
            <li
              key={v.id}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface)]"
            >
              <div className="flex items-center justify-between gap-2 px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggle(v.id)}
                  className="flex min-w-0 flex-1 items-center gap-3 text-left"
                >
                  {expanded === v.id ? (
                    <ChevronDown className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                  ) : (
                    <ChevronRight className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                  )}
                  <EntityIcon name={v.name} />
                  <div className="min-w-0">
                    <p className="truncate font-medium">{v.name}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {v.is_global
                        ? "catálogo"
                        : v.category ?? "proveedor propio"}
                    </p>
                  </div>
                </button>
                {!v.is_global ? (
                  <button
                    type="button"
                    onClick={() => removeVendor(v.id)}
                    aria-label={`Eliminar ${v.name}`}
                    className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                ) : null}
              </div>

              {expanded === v.id ? (
                <div className="border-t border-[var(--border)] px-4 py-3">
                  <ServiceList
                    services={services[v.id] ?? []}
                    canWrite={!v.is_global}
                    onAdd={(name) => addService(v.id, name)}
                    onRemove={(serviceId) => removeService(v.id, serviceId)}
                  />
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ServiceList({
  services,
  canWrite,
  onAdd,
  onRemove,
}: {
  services: Service[];
  canWrite: boolean;
  onAdd: (name: string) => void;
  onRemove: (serviceId: string) => void;
}) {
  const [name, setName] = useState("");
  return (
    <div className="flex flex-col gap-2">
      {services.length === 0 ? (
        <p className="text-sm text-[var(--muted-foreground)]">Sin servicios.</p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {services.map((s) => (
            <li
              key={s.id}
              className="flex items-center justify-between text-sm"
            >
              <span>{s.name}</span>
              {canWrite ? (
                <button
                  type="button"
                  onClick={() => onRemove(s.id)}
                  aria-label={`Eliminar ${s.name}`}
                  className="text-[var(--muted-foreground)] hover:text-[var(--negative)]"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {canWrite ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onAdd(name);
            setName("");
          }}
          className="mt-1 flex gap-2"
        >
          <Input
            aria-label="Nuevo servicio"
            placeholder="Nuevo servicio…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="text-sm"
          />
          <Button type="submit" variant="ghost" disabled={!name.trim()}>
            <Plus className="h-4 w-4" />
          </Button>
        </form>
      ) : (
        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          Los servicios del catálogo global no se pueden editar.
        </p>
      )}
    </div>
  );
}
