import Link from "next/link";
import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { BrandWordmark } from "@/components/brand";

export const metadata: Metadata = { title: "Ingresar" };

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6 py-12">
      <div className="mb-8">
        <BrandWordmark />
      </div>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">Ingresá</h1>
      <p className="mb-6 text-sm text-[var(--muted-foreground)]">
        Accedé a tus costos y aplicaciones.
      </p>
      <AuthForm mode="login" />
      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        ¿No tenés cuenta?{" "}
        <Link href="/register" className="text-[var(--primary)] hover:underline">
          Creá una
        </Link>
      </p>
    </main>
  );
}
