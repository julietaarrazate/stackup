# ADR-002: Database

Status: Accepted
Date: 2026-08-19

## Context

The user's rules are explicit and non-negotiable: **Render's free
PostgreSQL must never be used as the primary datastore**, SQLite must never
be used in production, and no critical persistent data may live on Render's
ephemeral filesystem.

Verified against current docs (August 2026): Render free Postgres instances
expire 30 days after creation, with a 14-day grace period to upgrade before
Render **deletes the database and all its data**. That is incompatible with
storing real cost/workspace data.

## Decision

PostgreSQL is hosted on **Neon**, provisioned as a single project with
branches used for preview/staging environments (Neon branches are
copy-on-write, cheap to create/destroy, which fits Vercel/Render preview
workflows later).

- Driver: `asyncpg` via SQLAlchemy 2.x async engine.
- Schema managed exclusively through Alembic migrations — no manual
  production schema edits.
- Render hosts only compute (FastAPI web service + worker); it never owns
  persistent data on its own filesystem or its own Postgres offering.

## Free tier facts (verified August 2026)

- Neon Free: 100 CU-hours/month compute, 0.5 GB storage per project, up to
  10 branches per project, up to 100 projects, autoscaling to 2 CU,
  scale-to-zero when idle.
- Risk: Neon free-plan projects inactive for an extended period (Neon's
  published policy has referenced ~90 days) may be subject to deletion.
  Mitigated by keeping the project active (real usage) and by upgrading
  before letting it go idle for that long.

## Consequences

- Scale-to-zero means occasional cold-start latency on the DB connection
  after idle periods — acceptable for MVP traffic.
- Upgrading Neon from Free to a paid plan is a billing change only; the
  connection string, schema, and SQLAlchemy/Alembic setup are unaffected —
  satisfies the "Free → Paid without migrating the app" requirement.
- Local development uses a Neon branch (or local Postgres via Docker) —
  never SQLite — so behavior matches production.
