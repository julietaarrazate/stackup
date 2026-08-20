import Link from "next/link";
import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { ChevronRight } from "lucide-react";
import { getCurrentUser, listWorkspaces } from "@/lib/session";
import { BrandWordmark } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import { CreateWorkspace } from "@/components/create-workspace";
import { EditDisplayName } from "@/components/edit-display-name";

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
        <EditDisplayName fullName={user.full_name} email={user.email} />
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
              <li key={ws.id}>
                <Link
                  href={`/app/${ws.id}`}
                  className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 transition-colors hover:bg-[var(--surface-2)]"
                >
                  <div>
                    <p className="font-medium">{ws.name}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      /{ws.slug} · {ws.base_currency}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-[var(--muted-foreground)]" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="mt-auto border-t border-[var(--border)] py-6 text-sm text-[var(--muted-foreground)]">
        Entrá a un workspace para ver aplicaciones, costos y reportes.
      </footer>
    </main>
  );
}
