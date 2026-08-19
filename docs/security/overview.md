# Security Overview

Controls STACKUP implements or commits to, mapped to the requirements in
docs sections 26/44. Items not yet built name the phase that delivers them,
so this document tracks real state, not aspiration.

## Implemented in Phase 1

- **No secrets in the repo.** `.gitignore` excludes `.env*`; `.env.example`
  carries only placeholders; Alembic and Render blueprint read the DB URL
  from the environment, never from committed files.
- **Datastore guard (ADR-002).** The app refuses to boot in
  staging/production with a SQLite URL, preventing an accidental
  non-durable datastore.
- **CORS locked to one origin.** The API allows only the configured
  first-party BFF origin, not `*`.
- **Request correlation.** Every request gets a `request_id` (logged,
  echoed, attached to Sentry) for auditable tracing.
- **Health endpoints leak nothing.** `/health` and `/ready` return only
  status — no versions, connection strings, or stack traces (tested).
- **Safe logging.** Structured JSON logs; Sentry configured with
  `send_default_pii=False`.
- **Evidence upload validation** (Phase 6, ADR-006). Server-side
  MIME-allowlist (pdf/png/jpeg/webp) + size limit; the object is stored
  under a random key (never the user filename, which is kept as metadata
  only); private object store; downloads stream through an authorized
  endpoint (never a public URL); production requires R2 to be configured
  (the in-process backend is dev/test only).

## Committed for later phases (with phase)

- **Authentication** (Phase 2): `fastapi-users`, HttpOnly/Secure/SameSite
  session cookies via the BFF, no tokens in localStorage, password reset /
  email verification, session revocation (ADR-003).
- **Authorization & workspace isolation** (Phase 2): centralized policy
  module; every query filtered by the session-derived workspace set;
  cross-workspace access returns 404. Isolation proven by security tests
  (Phase 9): User A cannot read/modify/download Workspace B; viewer cannot
  mutate; member cannot manage ownership; manipulated IDs grant no
  horizontal access.
- **Rate limiting** (Phase 2): Redis-backed limits on auth endpoints
  (login, register, forgot-password).
- **CSRF** (Phase 2): SameSite=Lax + strict CORS + a custom header
  required on state-changing requests (double-submit).
- **Upload validation** (Phase 6): server-side MIME/extension/size checks;
  random storage keys; private bucket; signed URLs; never trust the
  client filename (ADR-006).
- **Security headers** (Phase 9): CSP and related headers via Next.js and
  FastAPI middleware.
- **Audit logging** (Phase 2+): `AuditEvent` for privileged mutations.

## Secret management

Secrets live only in provider dashboards (Vercel, Render, Neon, Upstash,
Cloudflare, Sentry) and are injected as environment variables. Rotation is
a dashboard operation; no secret is ever printed in logs or error output.
