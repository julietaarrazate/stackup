import Link from "next/link";
import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/forgot-password-form";
import { BrandWordmark } from "@/components/brand";

export const metadata: Metadata = { title: "Recuperar contraseña" };

export default function ForgotPasswordPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6 py-12">
      <div className="mb-8">
        <BrandWordmark />
      </div>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">
        Recuperar contraseña
      </h1>
      <p className="mb-6 text-sm text-[var(--muted-foreground)]">
        Ingresá tu email y te mandamos un enlace para restablecerla.
      </p>
      <ForgotPasswordForm />
      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        <Link href="/login" className="text-[var(--primary)] hover:underline">
          Volver al login
        </Link>
      </p>
    </main>
  );
}
