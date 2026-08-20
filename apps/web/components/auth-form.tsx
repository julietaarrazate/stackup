"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";

const schema = z.object({
  full_name: z.string().max(160).optional(),
  email: z.string().email("Ingresá un email válido."),
  password: z.string().min(8, "La contraseña debe tener al menos 8 caracteres."),
});

type FormValues = z.infer<typeof schema>;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setServerError(null);

    if (mode === "register") {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) {
        setServerError("No se pudo crear la cuenta. ¿Ya existe ese email?");
        return;
      }
    }

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(values),
    });
    if (!res.ok) {
      setServerError("Email o contraseña incorrectos.");
      return;
    }
    router.push("/app");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      {mode === "register" ? (
        <Field label="Nombre (opcional)" htmlFor="full_name">
          <Input
            id="full_name"
            autoComplete="name"
            placeholder="¿Cómo querés que te llamemos?"
            {...register("full_name")}
          />
        </Field>
      ) : null}
      <Field label="Email" htmlFor="email" error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="vos@ejemplo.com"
          {...register("email")}
        />
      </Field>
      <Field label="Contraseña" htmlFor="password" error={errors.password?.message}>
        <PasswordInput
          id="password"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          placeholder="••••••••"
          {...register("password")}
        />
        {mode === "login" ? (
          <Link
            href="/forgot-password"
            className="mt-1 self-end text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
          >
            ¿Olvidaste tu contraseña?
          </Link>
        ) : null}
      </Field>
      {serverError ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {serverError}
        </p>
      ) : null}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting
          ? "Un momento…"
          : mode === "login"
            ? "Ingresar"
            : "Crear cuenta"}
      </Button>
    </form>
  );
}
