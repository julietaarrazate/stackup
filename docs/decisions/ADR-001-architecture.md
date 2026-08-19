# ADR-001: Overall Architecture

Status: Accepted
Date: 2026-08-19

## Context

STACKUP needs to answer "what does my software actually cost" for multiple
workspaces, growing toward thousands of applications analyzed. It must be
real (persistent, multi-tenant, secure), not a demo, and the domain must
support future capabilities (GitHub repo analysis, invoice parsing, cost
forecasting) without a rewrite.

The user mandates: Next.js frontend, FastAPI backend, PostgreSQL on Neon,
Render for compute, object storage for evidence, Sentry for observability,
GitHub Actions for CI.

## Decision

Split the system into three deployable units sharing one repository
(monorepo, not a monolith):

1. **apps/web** — Next.js (App Router, TypeScript strict) on Vercel. Acts as
   a **BFF (Backend-for-Frontend)**: Server Components and Route Handlers
   call FastAPI server-side and forward cookies. The browser never talks to
   FastAPI directly and never sees backend secrets.
2. **apps/api** — FastAPI (async, SQLAlchemy 2.x, Alembic, Pydantic v2) on
   Render, exposing a versioned REST API under `/api/v1`. Owns all business
   rules, the Cost Engine, and authorization.
3. **worker** — same Python codebase as apps/api, different entrypoint
   (`arq` worker), deployed as a separate Render background worker service.
   Consumes jobs from a queue for GitHub analysis, document processing,
   imports, and future AI-assisted discovery.

Data flow: Browser → Next.js (Vercel) → FastAPI (Render) → PostgreSQL
(Neon). Async work: FastAPI → Upstash Redis queue → Worker (Render) →
PostgreSQL / R2.

## Alternatives considered

- **Next.js API routes as the only backend (no FastAPI)**: rejected — user
  explicitly requires FastAPI, and Python is the natural home for future
  data-heavy work (repo analysis, invoice parsing, ML-assisted discovery).
- **Browser calling FastAPI directly (no BFF)**: rejected — would force
  cross-origin cookies (`api.stackup.ar` vs `stackup.ar`) with weaker
  SameSite guarantees and would expose backend URLs/errors directly to the
  client. A thin BFF keeps session handling server-side and centralizes
  CORS to a single first-party origin.
- **Separate repositories per app**: rejected for now — a monorepo keeps
  the domain model, ADRs, and CI atomic while the team is a single
  developer; nothing here blocks splitting later if needed.

## Consequences

- Every request that needs data makes one extra network hop (Next.js →
  FastAPI) versus calling FastAPI directly. Acceptable: this hop is
  server-to-server (low latency) and buys us a materially simpler and
  safer auth model (see ADR-003).
- The worker and API share domain code, so a bug fix in the Cost Engine or
  models applies to both without duplication — but the two services must
  be deployed together when domain/model code changes.
- CI must build and test all three units independently.
