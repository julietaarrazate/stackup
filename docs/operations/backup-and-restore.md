# Backup & Restore / Disaster Recovery

Do not rely solely on the provider's automatic backups (docs section 29).
This document is the plan; the restore drill must be executed and verified
before STACKUP is declared production-ready (that item is tracked as
pending until Phase 9).

## What must be recoverable

1. **PostgreSQL (Neon)** — all workspace/cost data. Primary asset.
2. **Object storage (R2)** — evidence files (Phase 6+).

## Backup strategy

### PostgreSQL (Neon)

- **Provider-side:** Neon retains history and supports point-in-time
  restore within the plan's retention window (shorter on the free plan —
  see `FREE_TIER.md`). This is the first line, not the only line.
- **Independent, off-provider:** a scheduled `pg_dump` to R2, so a
  recovery does not depend on Neon being healthy:

  ```bash
  pg_dump "$DATABASE_URL_SYNC" --format=custom --file=stackup-$(date +%F).dump
  # upload the dump to a private R2 bucket (separate from evidence)
  ```

  `DATABASE_URL_SYNC` is the non-async (`postgresql://`) form of the Neon
  URL. This job is automated as a scheduled worker task in Phase 7; until
  then it is run manually and documented here.

### Object storage (R2)

- R2 objects are immutable once written (new `storage_key` per upload).
  Evidence metadata lives in Postgres, so a Postgres restore plus the R2
  bucket reconstitutes the full picture.

## Retention (target)

- Daily dumps kept 7 days, weekly kept 4 weeks, monthly kept 6 months.
  Tunable; documented so it is a decision, not an accident.

## Restore procedure (PostgreSQL)

1. Provision a fresh Neon branch/project (never restore over the live DB
   first — restore into a new target and verify).
2. `pg_restore --clean --if-exists --dbname "$TARGET_URL" stackup-YYYY-MM-DD.dump`
3. Run `alembic current` to confirm the schema version matches the app.
4. Point a staging deployment at the restored DB and run the E2E smoke
   suite (Phase 9) before promoting.

## RPO / RTO (targets)

- **RPO** (max acceptable data loss): 24h with daily dumps; minutes if
  relying on Neon PITR within retention.
- **RTO** (max acceptable downtime to restore): a few hours — provision
  target, restore dump, re-point app.

These targets are revisited before production; the restore drill in Phase 9
validates that RTO is actually achievable, not just estimated.
