import { forwardRef } from "react";

type Variant = "primary" | "ghost" | "danger";

const base =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90",
  ghost:
    "border border-[var(--border)] bg-transparent text-[var(--foreground)] hover:bg-[var(--surface-2)]",
  danger:
    "border border-[var(--border)] bg-transparent text-[var(--negative)] hover:bg-[var(--surface-2)]",
};

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }
>(function Button({ variant = "primary", className, ...props }, ref) {
  return (
    <button
      ref={ref}
      className={`${base} ${variants[variant]} ${className ?? ""}`}
      {...props}
    />
  );
});
