# Deployment

See ADR-001 (architecture) and ADR-007 (regions).

## Targets

| Unit | Provider | Config |
|---|---|---|
| `apps/web` (Next.js) | Vercel | `apps/web/vercel.json`, root directory `apps/web` |
| `apps/api` (FastAPI) | Render (web service, region Virginia) | `render.yaml` |
| Worker (arq) | Render (worker, Virginia) — Phase 7 | `render.yaml` (commented until Phase 7) |
| PostgreSQL | Neon (`aws-us-east-1`) | connection string in `DATABASE_URL` |
| Redis | Upstash — Phase 5+ | `REDIS_URL` |
| Object storage | Cloudflare R2 — Phase 6 | `STORAGE_*` |

## Environment variables

Set per environment in each provider's dashboard; never commit secrets.
Reference: `.env.example`. Backend needs `ENVIRONMENT`, `DATABASE_URL`,
`FRONTEND_ORIGIN`, and optionally `SENTRY_DSN`. Frontend needs
`API_BASE_URL`.

## CI gate

`.github/workflows/ci.yml` runs on every PR and on push to `main`:

- backend: ruff check + format check, mypy strict, pytest, `alembic upgrade
  head`, `alembic check` (no drift);
- frontend: lint, typecheck, build.

Nothing merges to `main` (and therefore nothing deploys) until these pass —
branch protection on `main` enforces it.

## Database migrations

Migrations run as an **explicit release step**, never inside web-process
startup (avoids races between instances — ADR/Phase 1 note):

```bash
cd apps/api
uv run alembic upgrade head
```

On Render this is a one-off Job (free plan) or `preDeployCommand` (paid).
Production schema is never edited by hand — every change is a migration.

## Domain (stackup.ar)

DNS is not assumed to be configured. When ready:

- `app.stackup.ar` → Vercel (frontend).
- `api.stackup.ar` → Render (backend).
- Session cookie is scoped to `.stackup.ar` so it is valid on both
  subdomains (ADR-003).
- `FRONTEND_ORIGIN` (backend CORS) and `API_BASE_URL` (frontend BFF) must
  point at the matching environment's URLs; preview/staging use their own
  values, never the production ones.

## Rollback

- Vercel: promote a previous deployment (instant rollback in the
  dashboard).
- Render: redeploy a previous image/commit.
- Database: a migration rollback is `alembic downgrade -1`, but prefer
  forward-fix migrations in production; destructive downgrades are a last
  resort and must be tested against a Neon branch first.
