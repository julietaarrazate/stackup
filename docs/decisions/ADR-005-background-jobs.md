# ADR-005: Background Jobs

Status: Accepted
Date: 2026-08-19

## Context

Future work (GitHub repository analysis, dependency detection, invoice/
document parsing, provider synchronization) must never run inside an HTTP
request. We need a queue + worker architecture from Phase 1, even though
the only Phase-7 job implemented initially may be small.

## Decision

- Queue/broker: **Upstash Redis** (free tier: 256 MB, 500K commands/month,
  10 GB bandwidth/month, no cold start, persistent — unlike Render's free
  Key Value, which is 25 MB and explicitly documented as in-memory data
  lost on every restart/redeploy, unacceptable for a job queue that must
  survive a deploy).
- Job library: **arq** — asyncio-native, lightweight, integrates directly
  with the same async SQLAlchemy session/domain code used by FastAPI,
  avoiding the heavier Celery + broker + beat scheduler stack for a
  single-worker MVP.
- Worker deployment: a second Render service (background worker, not web
  service) running `arq stackup_api.worker.WorkerSettings`, sharing the
  `apps/api` codebase and Python dependencies.

### Retry / idempotency / DLQ policy

- Every job payload carries an `idempotency_key` (derived from
  `source + external_id + operation` where applicable). Handlers upsert on
  that key so re-running a job never duplicates data (imports, GitHub
  analysis results, invoice parsing).
- `arq` retry: exponential backoff, max 5 attempts per job by default,
  configurable per job type.
- Jobs that exhaust retries are recorded in a `BackgroundJob` table
  (status=`failed`, last_error, attempt_count) rather than silently
  dropped — this is our dead-letter mechanism, queryable and
  re-triggerable, instead of relying on Redis-side DLQ semantics that
  would be lost if Redis data expired.
- Per-job timeout enforced by `arq`'s `job_timeout`; jobs must be safe to
  kill mid-execution (idempotent on resume).
- Observability: job start/end/failure logged with `request_id`/`job_id`
  and reported to Sentry on failure.

## Consequences

- Redis is a broker/signal only — the durable source of truth for job
  state is Postgres (`BackgroundJob` row), so even if Redis data were lost
  we can detect and re-enqueue stuck jobs instead of losing them silently.
- Two Render services (web + worker) both need the Neon connection and
  Upstash credentials — documented in `.env.example` for both.
