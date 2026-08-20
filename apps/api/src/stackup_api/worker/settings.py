"""arq worker entrypoint (Phase 7, ADR-005).

A second Render service runs this:
`uv run arq stackup_api.worker.settings.WorkerSettings`
Shares the apps/api codebase and the same DATABASE_URL as the web service;
needs its own REDIS_URL (Upstash) to connect to the queue.
"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron

from stackup_api.core.config import get_settings
from stackup_api.core.observability import init_sentry
from stackup_api.worker.tasks import auto_end_expired_costs


def _redis_settings() -> RedisSettings:
    settings = get_settings()
    if not settings.redis_url:
        raise RuntimeError(
            "REDIS_URL is not set — the worker cannot start without Upstash "
            "Redis (ADR-005)."
        )
    return RedisSettings.from_dsn(settings.redis_url)


async def _on_startup(ctx: dict[str, Any]) -> None:
    init_sentry(get_settings())


class WorkerSettings:
    functions = [auto_end_expired_costs]
    cron_jobs = [
        # Daily at 03:00 UTC — low-traffic hour, well clear of any request load.
        cron(auto_end_expired_costs, hour=3, minute=0, max_tries=5),
    ]
    on_startup = _on_startup
    redis_settings = _redis_settings()
    job_timeout = 300
    max_jobs = 10
