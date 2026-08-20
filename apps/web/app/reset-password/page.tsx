import Link from "next/link";
import type { Metadata } from "next";
import { ResetPasswordForm } from "@/components/reset-password-form";
import { BrandWordmark } from "@/components/brand";

export const metadata: Metadata = { title: "Restablecer contraseña" };

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6 py-12">
      <div className="mb-8">
        <BrandWordmark />
      </div>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">
        Nueva contraseña
      </h1>
      <p className="mb-6 text-sm text-[var(--muted-foreground)]">
        Elegí una contraseña nueva para tu cuenta.
      </p>
      <ResetPasswordForm token={token ?? ""} />
      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        <Link href="/login" className="text-[var(--primary)] hover:underline">
          Volver al login
        </Link>
      </p>
    </main>
  );
}
