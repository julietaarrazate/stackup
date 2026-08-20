"""Background job execution tracking (Phase 7, ADR-005).

Wraps a job's actual work with a durable `BackgroundJob` row keyed by
`idempotency_key`: a job that already succeeded for that key is skipped, not
re-run, and one that fails is left in a queryable `failed` state (our
dead-letter mechanism) instead of vanishing if Redis loses the queue. Retries
themselves are arq's job (max_tries on the cron/enqueue call); this module
only tracks outcome and exposes it durably in Postgres.
"""

from __future__ import annotations

import datetime
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from stackup_api.core.config import get_settings
from stackup_api.core.db import SessionLocal
from stackup_api.core.logging import get_logger
from stackup_api.models.background_job import BackgroundJob
from stackup_api.models.enums import JobStatus

logger = get_logger(__name__)

_MAX_ERROR_LENGTH = 2000


async def run_tracked_job(
    *,
    job_type: str,
    idempotency_key: str,
    run: Callable[[], Awaitable[dict[str, Any]]],
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, Any]:
    async with session_factory() as session:
        job = await session.scalar(
            select(BackgroundJob).where(
                BackgroundJob.idempotency_key == idempotency_key
            )
        )
        if job is not None and job.status == JobStatus.succeeded:
            logger.info(
                "job.skipped_already_succeeded",
                job_type=job_type,
                idempotency_key=idempotency_key,
            )
            return job.result or {}

        if job is None:
            job = BackgroundJob(
                job_type=job_type,
                idempotency_key=idempotency_key,
                status=JobStatus.running,
                attempt_count=1,
            )
            session.add(job)
        else:
            job.status = JobStatus.running
            job.attempt_count += 1
        job.started_at = datetime.datetime.now(datetime.UTC)
        job.last_error = None
        await session.commit()
        job_id = job.id

    logger.info("job.started", job_type=job_type, idempotency_key=idempotency_key)
    try:
        result = await run()
    except Exception as exc:
        async with session_factory() as session:
            failed = await session.get(BackgroundJob, job_id)
            if failed is not None:
                failed.status = JobStatus.failed
                failed.last_error = str(exc)[:_MAX_ERROR_LENGTH]
                failed.finished_at = datetime.datetime.now(datetime.UTC)
                await session.commit()
        logger.error(
            "job.failed",
            job_type=job_type,
            idempotency_key=idempotency_key,
            error=str(exc),
        )
        if get_settings().sentry_dsn:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        raise

    async with session_factory() as session:
        done = await session.get(BackgroundJob, job_id)
        if done is not None:
            done.status = JobStatus.succeeded
            done.result = result
            done.finished_at = datetime.datetime.now(datetime.UTC)
            await session.commit()
    logger.info(
        "job.succeeded",
        job_type=job_type,
        idempotency_key=idempotency_key,
        result=result,
    )
    return result
