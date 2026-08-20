"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    // Always show success — the backend never reveals whether the email exists.
    await fetch("/api/auth/forgot-password", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setBusy(false);
    setDone(true);
  }

  if (done) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Si existe una cuenta con ese email, te enviamos un enlace para
        restablecer la contraseña. Revisá tu bandeja de entrada.
      </p>
    );
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <Field label="Email" htmlFor="email">
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="vos@ejemplo.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </Field>
      <Button type="submit" disabled={busy || !email}>
        {busy ? "Enviando…" : "Enviar enlace"}
      </Button>
    </form>
  );
}
