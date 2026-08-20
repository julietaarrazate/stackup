"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AppWindow,
  ArrowLeft,
  BarChart3,
  Building2,
  Check,
  ChevronDown,
  LayoutDashboard,
  Plug,
  Receipt,
  Settings,
  Users,
} from "lucide-react";
import { BrandMark, BrandWordmark } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import type { Workspace } from "@/lib/session";

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
  mobile?: boolean;
};

function navItems(workspaceId: string): NavItem[] {
  const base = `/app/${workspaceId}`;
  return [
    { href: base, label: "Resumen", icon: LayoutDashboard, exact: true, mobile: true },
    {
      href: `${base}/applications`,
      label: "Aplicaciones",
      icon: AppWindow,
      mobile: true,
    },
    { href: `${base}/costs`, label: "Costos", icon: Receipt, mobile: true },
    { href: `${base}/vendors`, label: "Proveedores", icon: Building2 },
    { href: `${base}/reports`, label: "Reportes", icon: BarChart3, mobile: true },
    { href: `${base}/integrations`, label: "Integraciones", icon: Plug },
    { href: `${base}/members`, label: "Miembros", icon: Users },
    { href: `${base}/settings`, label: "Ajustes", icon: Settings, mobile: true },
  ];
}

function isActive(pathname: string, item: NavItem): boolean {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

export function WorkspaceShell({
  workspace,
  workspaces,
  userName,
  children,
}: {
  workspace: Workspace;
  workspaces: Workspace[];
  userName: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const items = navItems(workspace.id);
  const mobileItems = items.filter((i) => i.mobile);
  const [switcherOpen, setSwitcherOpen] = useState(false);

  return (
    <div className="lg:flex lg:min-h-dvh">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-[var(--border)] lg:bg-[var(--surface)] lg:px-5 lg:py-6">
        <Link href="/app" className="mb-6">
          <BrandWordmark />
        </Link>

        <div className="relative mb-6">
          <button
            type="button"
            onClick={() => setSwitcherOpen((o) => !o)}
            aria-expanded={switcherOpen}
            className="flex w-full items-center justify-between gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-left hover:bg-[var(--surface-2)]"
          >
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold">
                {workspace.name}
              </span>
              <span className="block text-xs text-[var(--muted-foreground)]">
                {workspace.base_currency}
              </span>
            </span>
            <ChevronDown className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
          </button>
          {switcherOpen ? (
            <div className="absolute left-0 right-0 top-full z-20 mt-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg">
              {workspaces.map((w) => (
                <Link
                  key={w.id}
                  href={`/app/${w.id}`}
                  onClick={() => setSwitcherOpen(false)}
                  className="flex items-center justify-between gap-2 px-3 py-2 text-sm hover:bg-[var(--surface-2)]"
                >
                  <span className="truncate">{w.name}</span>
                  {w.id === workspace.id ? (
                    <Check className="h-3.5 w-3.5 shrink-0 text-[var(--primary)]" />
                  ) : null}
                </Link>
              ))}
              <Link
                href="/app"
                onClick={() => setSwitcherOpen(false)}
                className="flex items-center gap-1.5 border-t border-[var(--border)] px-3 py-2 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Todos los workspaces
              </Link>
            </div>
          ) : null}
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
        </nav>

        <div className="mt-auto flex flex-col gap-3 border-t border-[var(--border)] pt-4">
          <p className="truncate text-xs text-[var(--muted-foreground)]">
            {userName}
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
          {mobileItems.map((item) => {
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
