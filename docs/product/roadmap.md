# STACKUP — Implementation Roadmap

Phases as scoped with the product owner. Each phase ends with: tests run,
lint run, typecheck run, build run, changes reviewed, docs updated, a
report of what works, and an explicit list of what's pending — before
moving to the next phase.

- **Phase 0 — Architecture & ADRs** (this PR): architecture proposal,
  ADR-001..009, domain model doc, roadmap, free-tier audit.
- **Phase 1 — Project foundation**: `apps/web` and `apps/api` scaffolds,
  Alembic baseline migration, GitHub Actions CI (lint/typecheck/test/build
  for both apps), basic Render + Vercel deployment wiring, Sentry +
  `/health` + `/ready`.
- **Phase 2 — Auth + Workspace + RBAC**: `fastapi-users` integration,
  workspace creation, WorkspaceMember + role policy module, session cookie
  flow through the Next.js BFF, rate limiting on auth endpoints.
- **Phase 3 — Applications + Environments + Vendors + Services**: CRUD +
  authorization + seed data (dev/test only).
- **Phase 4 — CostItems + Cost Engine + CostHistory**: the core money
  model, Cost Engine with exhaustive unit/property tests.
- **Phase 5 — Dashboard + Reports**: overview, cost by application/vendor/
  category, evolution, confirmed vs estimated — backend aggregation, no
  client-side recomputation.
- **Phase 6 — Expenses + Evidence**: R2 upload/download, signed URLs,
  upload validation.
- **Phase 7 — Background Jobs**: `arq` + Upstash Redis wiring, first real
  job (e.g. scheduled cost-history snapshotting or evidence virus/MIME
  re-validation), `BackgroundJob` table, retry/DLQ per ADR-005.
- **Phase 8 — GitHub integration foundation**: OAuth connection + repo
  file fetch + detection heuristics (package.json, requirements.txt,
  Dockerfile, render.yaml, vercel.json, etc.) producing confirmable
  `Detection` records — never auto-created CostItems.
- **Phase 9 — Hardening**: full E2E suite (Playwright), workspace-isolation
  security tests, performance pass, backup/restore drill, production
  readiness checklist per the acceptance criteria below.

## MVP acceptance criteria (tracked against the 31 items requested)

Tracked as a checklist in each phase's report; not duplicated here to
avoid drift — see the PR description of the phase that claims each item
done.
