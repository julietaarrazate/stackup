import Link from "next/link";
import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { BrandWordmark } from "@/components/brand";

export const metadata: Metadata = { title: "Crear cuenta" };

export default function RegisterPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6 py-12">
      <div className="mb-8">
        <BrandWordmark />
      </div>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">Creá tu cuenta</h1>
      <p className="mb-6 text-sm text-[var(--muted-foreground)]">
        Empezá a medir cuánto te cuesta tu software.
      </p>
      <AuthForm mode="register" />
      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        ¿Ya tenés cuenta?{" "}
        <Link href="/login" className="text-[var(--primary)] hover:underline">
          Ingresá
        </Link>
      </p>
    </main>
  );
}
