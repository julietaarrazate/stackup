# STACKUP

> Know what your software really costs.

STACKUP is a multi-tenant SaaS for tracking, analyzing, and projecting the
real cost of running an application or startup: infrastructure, software,
APIs, vendors, and domains — with confirmed vs. estimated vs. projected
costs, historical price changes, and reporting by application, vendor, and
category.

## Status

Early architecture phase. See `docs/product/roadmap.md` for the phased
implementation plan (Phase 0 of 9 in progress).

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
