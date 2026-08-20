"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AppWindow,
  ArrowLeft,
  BarChart3,
  LayoutDashboard,
  Plug,
  Receipt,
  Settings,
} from "lucide-react";
import { BrandMark, BrandWordmark } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import type { Workspace } from "@/lib/session";

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
};

function navItems(workspaceId: string): NavItem[] {
  const base = `/app/${workspaceId}`;
  return [
    { href: base, label: "Overview", icon: LayoutDashboard, exact: true },
    { href: `${base}/applications`, label: "Aplicaciones", icon: AppWindow },
    { href: `${base}/costs`, label: "Costos", icon: Receipt },
    { href: `${base}/reports`, label: "Reportes", icon: BarChart3 },
    { href: `${base}/settings`, label: "Ajustes", icon: Settings },
  ];
}

function isActive(pathname: string, item: NavItem): boolean {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

export function WorkspaceShell({
  workspace,
  userEmail,
  children,
}: {
  workspace: Workspace;
  userEmail: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const items = navItems(workspace.id);

  return (
    <div className="lg:flex lg:min-h-dvh">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-[var(--border)] lg:bg-[var(--surface)] lg:px-5 lg:py-6">
        <Link href="/app" className="mb-1">
          <BrandWordmark />
        </Link>
        <Link
          href="/app"
          className="mb-6 inline-flex items-center gap-1 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Todos los workspaces
        </Link>

        <div className="mb-6">
          <p className="truncate text-sm font-semibold">{workspace.name}</p>
          <p className="text-xs text-[var(--muted-foreground)]">
            /{workspace.slug} · {workspace.base_currency}
          </p>
        </div>

        <nav className="flex flex-col gap-1">
          {items.map((item) => {
            const active = isActive(pathname, item);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--foreground)]"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
          <span className="mt-1 flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[var(--muted-foreground)] opacity-60">
            <Plug className="h-4 w-4" />
            Integraciones
            <span className="ml-auto rounded-full border border-[var(--border)] px-1.5 py-0.5 text-[10px]">
              pronto
            </span>
          </span>
        </nav>

        <div className="mt-auto flex flex-col gap-3 border-t border-[var(--border)] pt-4">
          <p className="truncate text-xs text-[var(--muted-foreground)]">
            {userEmail}
          </p>
          <LogoutButton />
        </div>
      </aside>

      <div className="flex min-h-dvh flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3 lg:hidden">
          <Link href="/app" className="flex items-center gap-2">
            <BrandMark className="h-6 w-6" />
            <div>
              <p className="text-sm font-semibold leading-tight">
                {workspace.name}
              </p>
              <p className="text-[11px] leading-tight text-[var(--muted-foreground)]">
                {workspace.base_currency}
              </p>
            </div>
          </Link>
          <LogoutButton />
        </header>

        <main className="mx-auto w-full max-w-5xl flex-1 px-4 pb-24 pt-4 lg:px-10 lg:pb-10 lg:pt-8">
          {children}
        </main>

        {/* Mobile bottom tab bar — reachable one-handed */}
        <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-[var(--border)] bg-[var(--surface)]/95 backdrop-blur lg:hidden">
          {items.map((item) => {
            const active = isActive(pathname, item);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium ${
                  active
                    ? "text-[var(--primary)]"
                    : "text-[var(--muted-foreground)]"
                }`}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
