# STACKUP — Architecture Overview

> "Know what your software really costs."

STACKUP is a multi-tenant SaaS that answers what an application or startup
actually costs in software, infrastructure, vendors, and services — with
real, persisted, workspace-isolated data.

## Components

```
Browser
  │  HTTPS
  ▼
Next.js (apps/web) — Vercel
  │  server-side fetch, forwards session cookie
  ▼
FastAPI (apps/api) — Render (web service)
  │                         │
  ▼                         ▼
PostgreSQL (Neon)      Upstash Redis (queue/cache/rate-limit)
                            │
                            ▼
                        Worker (apps/api, arq entrypoint) — Render (background worker)
                            │
                            ▼
                        PostgreSQL (Neon) / Cloudflare R2

Evidence files ──────────────────────────────▶ Cloudflare R2 (private, signed URLs)
Errors + performance ────────────────────────▶ Sentry (web + api)
CI (lint/typecheck/test/build/migrations/e2e) ▶ GitHub Actions
```

See the ADRs in `docs/decisions/` for the reasoning behind each choice:

- ADR-001 — overall architecture (BFF split)
- ADR-002 — database (Neon, never Render free Postgres)
- ADR-003 — authentication (fastapi-users, not Better Auth/NextAuth)
- ADR-004 — multi-tenancy & authorization
- ADR-005 — background jobs (arq + Upstash Redis)
- ADR-006 — object storage (Cloudflare R2)
- ADR-007 — deployment & regions (Render Virginia ↔ Neon aws-us-east-1)
- ADR-008 — observability (Sentry, request_id, /health, /ready)
- ADR-009 — money and currency modeling (Decimal/NUMERIC, no float)

## Why a BFF split instead of the browser calling FastAPI directly

Next.js Route Handlers proxy every authenticated call to FastAPI
server-side, forwarding the session cookie. This keeps:

- CORS to a single first-party origin (no cross-origin cookie edge cases).
- Backend URLs and error payloads out of the browser's network tab.
- One place (FastAPI) as the sole source of truth for sessions and
  authorization, reusable later by non-Next.js clients (mobile, CLI,
  future public API).

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript strict, Tailwind CSS, shadcn/ui, Recharts, React Hook Form + Zod, Playwright |
| Backend | FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic v2, `fastapi-users`, `arq`, pytest, Ruff, mypy |
| Database | PostgreSQL on Neon |
| Queue/cache | Upstash Redis |
| Storage | Cloudflare R2 |
| Observability | Sentry (web + api) |
| CI/CD | GitHub Actions → Vercel (web) / Render (api, worker) |

## Domain model

See `docs/product/domain-model.md` for full entity definitions. Core shape:

```
User ──< WorkspaceMember >── Workspace
                                 │
                                 ├──< Application ──< Environment
                                 │        │
                                 │        └──< CostItem >── Service ── Vendor
                                 │                 │
                                 │                 ├──< CostHistory
                                 │                 └──< Expense ── Evidence
                                 │
                                 └──< AuditEvent
```

## Cost Engine

A dedicated domain module (`apps/api/src/stackup_api/domain/cost_engine.py`)
is the single place that computes `monthly_equivalent`, `annualized_cost`,
`projected_cost`, and all cost aggregations (by application, vendor,
category, trend, change). It is pure, currency-aware, uses `Decimal`
throughout, and is covered by exhaustive unit + property tests (see
ADR-009 and the roadmap's Phase 4/9 testing requirements). This logic is
never duplicated in the frontend.

## Known limitations (see also `docs/operations/FREE_TIER.md`)

- No Render region in South America — see ADR-007.
- Vercel Hobby is non-commercial only — must upgrade to Pro before any
  commercial/paid use of STACKUP itself.
- Sentry free plan is a single user seat.
