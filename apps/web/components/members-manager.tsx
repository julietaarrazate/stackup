"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UserMinus, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Member } from "@/lib/session";

const ROLES = [
  ["viewer", "Viewer — solo lectura"],
  ["member", "Member — lee y escribe"],
  ["admin", "Admin — gestiona miembros"],
  ["owner", "Owner"],
] as const;

const ROLE_LABEL: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
  viewer: "Viewer",
};

export function MembersManager({
  workspaceId,
  members,
  currentUserId,
  canManage,
  isOwner,
}: {
  workspaceId: string;
  members: Member[];
  currentUserId: string;
  canManage: boolean;
  isOwner: boolean;
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}/members`;

  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assignableRoles = isOwner ? ROLES : ROLES.filter(([r]) => r !== "owner");

  async function addMember(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    setError(null);
    const res = await fetch(base, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: email.trim(), role }),
    });
    setBusy(false);
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      setError(
        body?.detail ??
          "No se pudo agregar. La persona debe tener una cuenta de STACKUP.",
      );
      return;
    }
    setEmail("");
    router.refresh();
  }

  async function changeRole(memberId: string, newRole: string) {
    setError(null);
    const res = await fetch(`${base}/${memberId}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ role: newRole }),
    });
    if (!res.ok) {
      setError("No se pudo cambiar el rol.");
      return;
    }
    router.refresh();
  }

  async function removeMember(memberId: string) {
    setError(null);
    const res = await fetch(`${base}/${memberId}`, { method: "DELETE" });
    if (!res.ok) {
      setError("No se pudo quitar al miembro.");
      return;
    }
    router.refresh();
  }

  return (
    <div className="flex flex-col gap-4">
      {canManage ? (
        <form
          onSubmit={addMember}
          className="flex flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4"
        >
          <p className="text-sm font-medium">Agregar miembro</p>
          <p className="text-xs text-[var(--muted-foreground)]">
            La persona ya debe tener una cuenta en STACKUP registrada con ese email.
          </p>
          <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
            <Field label="Email" htmlFor="member-email">
              <Input
                id="member-email"
                type="email"
                placeholder="persona@empresa.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Field label="Rol" htmlFor="member-role">
              <Select
                id="member-role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                {assignableRoles.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="flex items-end">
              <Button type="submit" disabled={busy || !email.trim()}>
                <UserPlus className="h-4 w-4" />
                {busy ? "Agregando…" : "Agregar"}
              </Button>
            </div>
          </div>
          {error ? (
            <p className="text-sm text-[var(--negative)]" role="alert">
              {error}
            </p>
          ) : null}
        </form>
      ) : null}

      <ul className="flex flex-col gap-2">
        {members.map((m) => (
          <li
            key={m.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
          >
            <div className="min-w-0">
              <p className="truncate font-medium">
                {m.email}
                {m.user_id === currentUserId ? (
                  <span className="ml-2 text-xs text-[var(--muted-foreground)]">
                    (vos)
                  </span>
                ) : null}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {canManage && (isOwner || m.role !== "owner") ? (
                <Select
                  aria-label={`Rol de ${m.email}`}
                  value={m.role}
                  onChange={(e) => changeRole(m.id, e.target.value)}
                  className="w-auto py-1.5 text-xs"
                >
                  {assignableRoles.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              ) : (
                <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]">
                  {ROLE_LABEL[m.role] ?? m.role}
                </span>
              )}
              {canManage && (isOwner || m.role !== "owner") ? (
                <button
                  type="button"
                  onClick={() => removeMember(m.id)}
                  aria-label={`Quitar a ${m.email}`}
                  className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)]"
                >
                  <UserMinus className="h-4 w-4" />
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
