# stackup-api

FastAPI backend for STACKUP. Owns the domain model, the Cost Engine,
authentication, and authorization. Deployed on Render; talks to PostgreSQL
on Neon and (later) Upstash Redis. See `../../docs/architecture/overview.md`.

## Local development

```bash
cd apps/api
uv sync --extra dev            # create .venv and install deps
cp ../../.env.example .env      # fill in DATABASE_URL etc.
uv run uvicorn stackup_api.main:app --reload
```

## Quality checks (what CI runs)

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run alembic upgrade head        # migration applies cleanly
uv run alembic check               # models match migrations (no drift)
```

## Layout

```
src/stackup_api/
  core/      config, logging, request context, db session
  domain/    pure business logic (Cost Engine, money) — no I/O
  models/    SQLAlchemy 2.x ORM
  schemas/   Pydantic request/response models
  api/v1/    versioned REST routers
  services/  orchestration between API and domain/persistence
  worker/    arq background-job entrypoint (Phase 7)
alembic/     migrations
tests/       unit + integration
```
