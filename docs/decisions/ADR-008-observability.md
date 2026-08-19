# ADR-008: Observability

Status: Accepted
Date: 2026-08-19

## Context

We need error tracking and basic performance monitoring on both frontend
and backend, plus health/readiness endpoints that don't leak sensitive
information, from Phase 1 onward.

## Decision

- **Sentry** on both `apps/web` (Next.js SDK) and `apps/api` (Python SDK,
  FastAPI integration), using the free Developer plan (verified August
  2026: 5,000 errors/month, 10,000 performance/tracing units/month, 30-day
  retention, **1 user seat only**, free forever).
- Every FastAPI request gets a `request_id` (generated or taken from an
  inbound `X-Request-Id` header), included in structured JSON logs and
  attached to the Sentry scope, so a single request can be traced across
  API logs, worker logs, and Sentry events.
- Endpoints:
  - `GET /health` — process is up; no DB/dependency check; used for
    Render's liveness probe.
  - `GET /ready` — checks DB connectivity (and Redis, once wired) without
    exposing connection strings, versions, or stack traces — returns only
    a boolean-ish status per dependency.
- Structured logging (JSON) to stdout, consumed by Render's log stream;
  no bespoke log storage in Phase 1.

## Consequences

- The 1-seat limit on Sentry's free plan means it stops being sufficient
  the moment a second person needs their own Sentry login — documented in
  `FREE_TIER.md` as an upgrade trigger, not a surprise later.
- Because `/health` and `/ready` are unauthenticated by necessity (probes
  don't carry session cookies), they must never return anything beyond a
  status — enforced by keeping their handlers deliberately minimal.
