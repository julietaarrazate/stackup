# STACKUP

> Know what your software really costs.

STACKUP is a multi-tenant SaaS for tracking, analyzing, and projecting the
real cost of running an application or startup: infrastructure, software,
APIs, vendors, and domains — with confirmed vs. estimated vs. projected
costs, historical price changes, and reporting by application, vendor, and
category.

## Status

All 9 roadmap phases are complete and merged to `main`, plus a round of
post-launch polish. Production is live on real infrastructure — Vercel
(frontend), Render (API + planned worker), Neon (Postgres), Cloudflare R2
(evidence storage), Resend (email), Redis Cloud (job queue, worker not
yet deployed), and a GitHub OAuth App (repo integration) are all
configured with real credentials. See `docs/product/roadmap.md` for the
phased plan, `docs/operations/production-readiness.md` for the current
done/pending checklist, and `docs/product/session-log.md` for a running
log of what changed each work session — read that log first when picking
this project back up, to avoid re-deriving context or asserting stale
status.

Working today: register, login, logout (revocable server-side sessions),
an editable display name, role-based access control, workspace-scoped
CRUD for applications, environments, vendors and services (shared global
vendor catalog plus workspace-private ones), **cost tracking** with a
pure Decimal Cost Engine (monthly-equivalent, annualized, append-only
price history, full mixed-currency support — a workspace can hold costs
in USD and ARS side by side, never summed together), inline edit/delete
for both costs and applications, a **dashboard** (total stack cost per
currency, change vs previous period, cost by category / application /
vendor broken out per currency in use, confirmed vs estimated, a monthly
evolution chart, recent changes with es-AR day/month/year dates — all
aggregated in the backend), **expenses & evidence** — record real
payments against a cost and attach validated invoice/receipt files stored
privately in Cloudflare R2 (downloads stream through an authorized
endpoint, never a public URL), and a **GitHub integration** (OAuth
connect, repo scan, heuristic vendor/service detections that require
manual confirmation before becoming a cost). Everything runs through a
Next.js BFF in front of FastAPI, is CI-gated (lint, typecheck, mypy
strict, pytest, Playwright E2E, `alembic check`), and is verified
end-to-end.

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
- `docs/product/session-log.md` — running log of what shipped each work
  session, and what's still open — read this first
- `docs/operations/production-readiness.md` — current done/pending
  checklist against a production launch
- `docs/operations/FREE_TIER.md` — free-tier limits and upgrade paths for
  every infrastructure provider in use
