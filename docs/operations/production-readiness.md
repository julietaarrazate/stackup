# Production Readiness Checklist

Snapshot as of Phase 9 (hardening) + post-launch credential rollout. See
`docs/product/session-log.md` for the running history. Re-check before
announcing STACKUP as generally available — this list is a decision
record, not a one-time gate.

## Done

- [x] **Architecture**: BFF (Next.js → FastAPI, browser never talks to the
  API directly), workspace multi-tenancy enforced at the query layer
  (`get_workspace_context`, 404 not 403 for non-members), RBAC
  (owner/admin/member/viewer) centralized in `core/policy.py`.
- [x] **Data integrity**: money is `Decimal`/`NUMERIC(14,2)` end to end,
  never a float, on the wire as a string (ADR-009). Currencies are never
  summed across each other.
- [x] **CI gate**: nothing merges to `main` without ruff, ruff format,
  mypy `--strict`, pytest, `alembic upgrade head`, `alembic check` (no
  drift), frontend lint/typecheck/build, and now the Playwright E2E suite
  — all required, branch-protected.
- [x] **E2E coverage**: a golden-path test proves register → workspace →
  vendor/service → application → cost composes correctly through the real
  browser and shows the right computed numbers on the dashboard; a second
  test proves a non-member gets a 404 with zero information leak about a
  workspace they don't belong to.
- [x] **Restore drill executed** (not just planned) — see
  `backup-and-restore.md`. It caught and fixed a real schema drift between
  deployed Neon and deployed code (migrations 0006/0007 had never been
  applied to production).
- [x] **Secrets**: OAuth tokens (GitHub) encrypted at rest, never
  plaintext; no secret has a default that works in staging/production
  (`Settings.validate_for_runtime` refuses to boot with `dev-insecure-
  change-me`, SQLite, or unconfigured R2 in `production`).
- [x] **Observability**: Sentry wired (backend + worker + frontend),
  gated on `SENTRY_DSN` so it's a no-op until configured; structured
  logging with `request_id`/`job_id` throughout.
- [x] **Uploads**: MIME/size validated server-side, random non-guessable
  storage keys (never the user's filename), authorized-download-only
  (never a public URL).

## Done since the Phase 9 snapshot

- [x] **Cloudflare R2**: bucket `stackup-evidence` + a scoped
  (read/write, single-bucket) API token created and set on `stackup-api`.
  Evidence uploads now persist to real object storage.
- [x] **Resend**: `RESEND_API_KEY` set. Password-reset/verification
  emails send for real.
- [x] **GitHub OAuth App**: `GITHUB_CLIENT_ID/SECRET` set. The
  integration is connectable, not just gracefully 404ing.
- [x] **`ENVIRONMENT=staging` → `production`** on `stackup-api`.
- [x] **Redis** (Redis Cloud free tier, not Upstash — functionally
  equivalent for our usage: Redis is a broker/signal only per ADR-005,
  Postgres stays the source of truth) — `REDIS_URL` obtained and
  documented, but see the worker gap right below before assuming the
  queue is actually live.

## Pending

- [ ] **`stackup-worker` Render service was never deployed.** `REDIS_URL`
  currently sits unused in `stackup-api`'s env (harmless — nothing there
  reads it) because Render's free tier doesn't include Background
  Workers, only Web Services, and paying for one was declined for now.
  Net effect: the daily `auto_end_expired_costs` job does not run
  anywhere. Not a correctness bug — costs can be marked "ended" manually
  in the UI — but it means nothing currently automates that. A
  zero-cost alternative (protected endpoint on `stackup-api` + an
  external free cron pinger) was proposed, not yet built. Do this before
  building renewal/expiry alerts, which need the same building block.
- [ ] **Migration-apply-on-deploy**: `alembic upgrade head` is not wired
  as a Render pre-deploy/release step (free-tier Render doesn't support
  it without a paid instance); migrations have been applied by hand via
  the Neon MCP for every phase so far, including migration
  `0008_user_full_name`. Add it as a paid-tier `preDeployCommand`, or
  keep the discipline of applying migrations *before* merging the PR
  that depends on them.
- [ ] **Custom domain** (`stackup.ar`) + cookie domain
  (`COOKIE_DOMAIN=.stackup.ar`) — currently running on the Render/Vercel
  default subdomains.
- [ ] **i18n toggle** (read the UI in English) — explicitly deferred by
  the product owner, Spanish-only is fine for now.
- [ ] **Renewal/expiry alerts** — no advance warning before a cost's
  `end_date` today (email or in-app). Scoping question open: how many
  days ahead, which channel(s). Blocked on the same scheduler gap as the
  worker item above.

## Deliberately not built yet (Phase 8 was the ceiling)

- Phase 8 GitHub integration is scanning-only: no OAuth token refresh
  flow, no webhook-driven re-scan, no GitHub App (uses an OAuth App with
  `repo` scope). Fine for the current single-connection-per-workspace
  scope; revisit if usage shows the OAuth token expiring or scope
  limitations become a real problem.
- No rate limiting beyond auth endpoints (`core/ratelimit.py` covers
  login/register/reset only). Acceptable at current scale; revisit before
  opening signups publicly.
- No load/perf testing against realistic data volumes — the Cost Engine
  and report aggregation are `O(n)` over a workspace's cost items with no
  pagination anywhere in the API. Fine at MVP scale (a workspace with
  dozens to low hundreds of costs); would need pagination + indexed
  aggregation before a workspace with thousands of cost items.
