import Link from "next/link";
import { BrandWordmark } from "@/components/brand";
import { Button } from "@/components/ui/button";

const QUESTIONS = [
  "¿Cuánto cuesta mi aplicación por mes?",
  "¿Qué proveedor representa el mayor costo?",
  "¿Cuánto es real y cuánto estimado?",
  "¿Cómo evolucionó el costo de mi stack?",
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-5xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <BrandWordmark />
        <nav className="flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost">Ingresar</Button>
          </Link>
          <Link href="/register">
            <Button>Crear cuenta</Button>
          </Link>
        </nav>
      </header>

      <section className="flex flex-1 flex-col justify-center py-16">
        <p className="mb-4 text-sm font-medium tracking-wide text-[var(--primary)]">
          Cost intelligence para software y startups
        </p>
        <h1 className="max-w-3xl text-balance text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Sabé cuánto te cuesta{" "}
          <span className="text-[var(--primary)]">realmente</span> tu software.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-[var(--muted-foreground)]">
          Registrá, analizá y proyectá los costos reales de infraestructura,
          servicios, APIs, herramientas y dominios de cada una de tus
          aplicaciones. Costos confirmados, estimados y proyectados — con
          historial y reportes.
        </p>

        <ul className="mt-10 grid max-w-3xl gap-3 sm:grid-cols-2">
          {QUESTIONS.map((q) => (
            <li
              key={q}
              className="tabular rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--foreground)]"
            >
              {q}
            </li>
          ))}
        </ul>
      </section>

      <footer className="border-t border-[var(--border)] py-6 text-sm text-[var(--muted-foreground)]">
        En construcción. La autenticación, el workspace y el panel llegan en las
        próximas fases del roadmap.
      </footer>
    </main>
  );
}
