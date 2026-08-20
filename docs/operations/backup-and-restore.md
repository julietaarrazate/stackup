# Backup & Restore / Disaster Recovery

## What must be recoverable

1. **PostgreSQL (Neon)** — all workspace/cost data. Primary asset.
2. **Object storage (R2)** — evidence files (Phase 6+).

## Backup strategy

### PostgreSQL (Neon)

Neon branching is the backup mechanism, not a supplement to one: every
branch is a full, independently-queryable copy of the database as of a
point in time, created in seconds without touching the live database. A
`pg_dump`-to-R2 job was considered for Phase 7 but deliberately dropped —
Render's native Python buildpack (`runtime: python`, no Dockerfile) does
not guarantee `postgresql-client`/`pg_dump` is present, so that job would
have been a plausible-looking but silently-broken safety net. Branch-based
restore needs nothing installed anywhere and was actually exercised (see
the drill below), which a hypothetical pg_dump job was not.

- **Point-in-time recovery**: `history_retention_seconds` on the
  `stackup-prod` project governs how far back a branch can be created from
  (currently the free-tier default — check `describe_project` for the live
  value; raise it if the retention window needs to be longer than that).
- **Ad hoc recovery point**: create a branch from the current default
  branch (or from a specific timestamp within the retention window) at any
  time, for any reason — before a risky migration, to investigate a data
  issue, or as part of a restore drill.

### Object storage (R2)

- R2 objects are immutable once written (new `storage_key` per upload).
  Evidence metadata lives in Postgres, so a Postgres restore plus the R2
  bucket reconstitutes the full picture.

## Restore procedure

1. Create a new branch (`create_branch`, optionally with `parentId`/a
   past timestamp) — never restore over the live database first.
2. Verify `alembic_version` matches the app's latest migration, and spot-
   check row counts / key tables to confirm the data looks right.
3. Point a staging deployment's `DATABASE_URL` at the new branch's
   connection string and run the app's test suite / a smoke pass against
   it before ever promoting a branch to production traffic.
4. Delete the drill/recovery branch once done (or set `expiresAt` at
   creation so it self-cleans) — a stray branch left after the drill
   never causes a false sense of "checked" the next time this doc is read.

## Restore drill — executed 2026-08-20

Ran a real drill against `stackup-prod` (project `young-thunder-27917663`),
not a hypothetical:

1. Created branch `restore-drill-phase9` (`expiresAt` set so it
   self-deletes ~24h later regardless).
2. **Found real drift**: the branch's `alembic_version` was
   `0005_evidence_expense` — two merged migrations (`0006_background_jobs`,
   `0007_github_integration`) had never been applied to the deployed
   database, only to local/CI SQLite. The `background_job`, `github_connection`,
   and `detection` tables did not exist in production despite the app code
   on `main` expecting them.
3. Verified the fix on the drill branch first (applied the two migrations'
   DDL, confirmed `alembic_version` reached `0007_github_integration` and
   that existing data was untouched — 1 user, 1 workspace, 9 vendors, 25
   services, all intact), then applied the same DDL to the actual default
   branch to close the drift for real.
4. Confirmed the default branch now reads `0007_github_integration`.

This is the process this document describes working end to end: a branch
reconstituted a queryable, verifiable copy of production, and that copy is
what caught a real, otherwise-invisible mismatch between deployed schema
and deployed code — not a drill that only exercises the happy path.

**Standing gap this drill surfaced**: nothing currently *fails a deploy*
when a new migration lands on `main` without being applied to the Neon
database Render points at — `alembic upgrade head` isn't wired into the
Render deploy (see `docs/operations/deployment.md`), and this container's
network policy blocks the direct Postgres port, so migrations have been
applied by hand via the Neon MCP for every phase so far. Before the next
schema change ships, either add `alembic upgrade head` as a Render
pre-deploy/release step, or keep applying migrations by hand *before*
merging the PR that depends on them — not after, as happened here.

## RPO / RTO (targets)

- **RPO** (max acceptable data loss): minutes — Neon's point-in-time
  recovery within `history_retention_seconds`, not a periodic dump.
- **RTO** (max acceptable downtime to restore): under 10 minutes to create
  a branch and verify it; the drill above took a few minutes end to end.
  Re-pointing `DATABASE_URL` at a promoted branch is the remaining step and
  is a Render dashboard change, not a data operation.
