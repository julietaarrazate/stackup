"use client";

import { forwardRef, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

/** Password input with an accessible show/hide toggle. */
export const PasswordInput = forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, "type">
>(function PasswordInput({ className, ...props }, ref) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
        ref={ref}
        type={visible ? "text" : "password"}
        className={`w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 pr-10 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus-visible:outline-2 focus-visible:outline-offset-2 ${className ?? ""}`}
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-pressed={visible}
        aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
      >
        {visible ? (
          <EyeOff className="h-4 w-4" />
        ) : (
          <Eye className="h-4 w-4" />
        )}
      </button>
    </div>
  );
});
