"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Github, RefreshCw, ScanSearch, Unplug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import type { Application, GitHubConnection } from "@/lib/session";

type Repo = { full_name: string; private: boolean; default_branch: string };

export function GitHubIntegration({
  workspaceId,
  connection,
  applications,
}: {
  workspaceId: string;
  connection: GitHubConnection | null;
  applications: Application[];
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}/integrations/github`;

  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function connect() {
    setConnecting(true);
    setError(null);
    const res = await fetch(`${base}/authorize`);
    setConnecting(false);
    if (!res.ok) {
      setError(
        res.status === 404
          ? "La integración con GitHub no está configurada en este servidor."
          : "No se pudo iniciar la conexión con GitHub.",
      );
      return;
    }
    const { authorize_url } = (await res.json()) as { authorize_url: string };
    window.location.href = authorize_url;
  }

  async function disconnect() {
    const res = await fetch(base, { method: "DELETE" });
    if (res.ok) router.refresh();
  }

  if (!connection) {
    return (
      <div className="flex flex-col gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          <p className="font-medium">Conectar GitHub</p>
        </div>
        <p className="text-sm text-[var(--muted-foreground)]">
          Conectá un repositorio para detectar automáticamente proveedores y
          servicios que ya estás pagando (Stripe, Sentry, Vercel, etc.) a partir
          de sus archivos de dependencias.
        </p>
        {error ? (
          <p className="text-sm text-[var(--negative)]" role="alert">
            {error}
          </p>
        ) : null}
        <div>
          <Button onClick={connect} disabled={connecting}>
            <Github className="h-4 w-4" />
            {connecting ? "Conectando…" : "Conectar GitHub"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          <p className="font-medium">Conectado como {connection.github_login}</p>
        </div>
        <button
          type="button"
          onClick={disconnect}
          aria-label="Desconectar GitHub"
          className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--negative)]"
        >
          <Unplug className="h-4 w-4" />
        </button>
      </div>
      <RepoScanner workspaceId={workspaceId} applications={applications} />
    </div>
  );
}

function RepoScanner({
  workspaceId,
  applications,
}: {
  workspaceId: string;
  applications: Application[];
}) {
  const router = useRouter();
  const base = `/api/v1/workspaces/${workspaceId}/integrations/github`;

  const [repos, setRepos] = useState<Repo[] | null>(null);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repo, setRepo] = useState("");
  const [applicationId, setApplicationId] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<number | null>(null);

  async function loadRepos() {
    setLoadingRepos(true);
    setError(null);
    const res = await fetch(`${base}/repos`);
    setLoadingRepos(false);
    if (!res.ok) {
      setError("No se pudieron cargar los repositorios.");
      return;
    }
    setRepos((await res.json()) as Repo[]);
  }

  async function scan(e: React.FormEvent) {
    e.preventDefault();
    if (!repo) return;
    setScanning(true);
    setError(null);
    setResult(null);
    const res = await fetch(`${base}/scan`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        repo_full_name: repo,
        application_id: applicationId || null,
      }),
    });
    setScanning(false);
    if (!res.ok) {
      setError("No se pudo escanear el repositorio.");
      return;
    }
    const detections = await res.json();
    setResult(detections.length);
    router.refresh();
  }

  if (repos === null) {
    return (
      <Button variant="ghost" onClick={loadRepos} disabled={loadingRepos}>
        <RefreshCw className="h-4 w-4" />
        {loadingRepos ? "Cargando repos…" : "Ver mis repositorios"}
      </Button>
    );
  }

  return (
    <form onSubmit={scan} className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Select
          aria-label="Repositorio"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
        >
          <option value="">Elegí un repositorio…</option>
          {repos.map((r) => (
            <option key={r.full_name} value={r.full_name}>
              {r.full_name}
              {r.private ? " (privado)" : ""}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Aplicación (opcional)"
          value={applicationId}
          onChange={(e) => setApplicationId(e.target.value)}
        >
          <option value="">Sin aplicación asociada</option>
          {applications.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </Select>
      </div>
      {error ? (
        <p className="text-sm text-[var(--negative)]" role="alert">
          {error}
        </p>
      ) : null}
      {result !== null ? (
        <p className="text-sm text-[var(--positive)]">
          {result === 0
            ? "No se encontraron señales nuevas en este repo."
            : `${result} señal${result === 1 ? "" : "es"} detectada${result === 1 ? "" : "s"} — revisalas abajo.`}
        </p>
      ) : null}
      <div>
        <Button type="submit" disabled={scanning || !repo}>
          <ScanSearch className="h-4 w-4" />
          {scanning ? "Escaneando…" : "Escanear repositorio"}
        </Button>
      </div>
    </form>
  );
}
