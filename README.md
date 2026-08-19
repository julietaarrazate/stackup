# STACKUP

> Know what your software really costs.

STACKUP is a multi-tenant SaaS for tracking, analyzing, and projecting the
real cost of running an application or startup: infrastructure, software,
APIs, vendors, and domains — with confirmed vs. estimated vs. projected
costs, historical price changes, and reporting by application, vendor, and
category.

## Status

Phase 4 of 9 complete (Phases 0–3 merged to `main`). See
`docs/product/roadmap.md` for the full phased plan. The dashboard and
reports arrive next (Phase 5).

Working today: register, login, logout (revocable server-side sessions),
role-based access control, workspace-scoped CRUD for applications,
environments, vendors and services (shared global vendor catalog), and
**cost tracking** — cost items with a pure, Decimal-based Cost Engine that
computes monthly-equivalent and annualized figures, plus an append-only
price history. All through a Next.js BFF in front of FastAPI, CI-gated and
verified end-to-end. A dev/test seed provides the vendor catalog plus
Oído/Cuadra/Stackup examples.

## Repository layout

```
apps/web/   Next.js frontend (Vercel) — App Router, TS strict, Tailwind, BFF
apps/api/   FastAPI backend + worker (Render) — SQLAlchemy 2.x, Alembic
docs/       architecture, ADRs, product, operations, security
.github/    CI (lint · typecheck · test · build · migrations)
render.yaml Render blueprint (compute only — DB is Neon, never Render)
```

## Getting started

Backend and frontend each have their own README with local-dev and
quality-check commands:

- `apps/api/README.md`
- `apps/web/README.md`

Copy `.env.example` to the per-app env files and fill in values (no real
secrets are committed).

## Documentation

- `docs/architecture/overview.md` — system architecture and tech stack
- `docs/decisions/` — Architecture Decision Records (ADRs)
- `docs/product/domain-model.md` — domain entities and invariants
- `docs/product/roadmap.md` — phased implementation plan
- `docs/operations/FREE_TIER.md` — free-tier limits and upgrade paths for
  every infrastructure provider in use

## Planned structure

```
apps/web/   Next.js frontend (Vercel)
apps/api/   FastAPI backend + background worker (Render)
```

Not yet scaffolded — see ADR-001 and Phase 1 of the roadmap.
