import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getCurrentUser, listWorkspaces } from "@/lib/session";
import { BrandWordmark } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import { CreateWorkspace } from "@/components/create-workspace";

export const metadata: Metadata = { title: "Inicio" };

export default async function AppHome() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const workspaces = await listWorkspaces();

  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <BrandWordmark />
        <LogoutButton />
      </header>

      <section className="py-6">
        <p className="text-sm text-[var(--muted-foreground)]">Sesión iniciada como</p>
        <p className="font-medium">{user.email}</p>
      </section>

      <section className="flex flex-col gap-4 py-4">
        <h1 className="text-xl font-semibold tracking-tight">Tus workspaces</h1>
        <CreateWorkspace />

        {workspaces.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center">
            <p className="font-medium">Todavía no tenés workspaces</p>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              Creá tu primer workspace para empezar a cargar aplicaciones y costos.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {workspaces.map((ws) => (
              <li
                key={ws.id}
                className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3"
              >
                <div>
                  <p className="font-medium">{ws.name}</p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    /{ws.slug} · {ws.base_currency}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="mt-auto border-t border-[var(--border)] py-6 text-sm text-[var(--muted-foreground)]">
        Aplicaciones, costos y reportes llegan en las próximas fases.
      </footer>
    </main>
  );
}
