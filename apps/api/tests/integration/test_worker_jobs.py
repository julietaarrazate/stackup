"""Background job tests (Phase 7, ADR-005): job tracking + the first real job."""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from stackup_api.models.background_job import BackgroundJob
from stackup_api.models.cost import CostItem
from stackup_api.models.enums import JobStatus
from stackup_api.services.jobs import run_tracked_job
from stackup_api.worker.tasks import auto_end_expired_costs
from tests.conftest import authed_client


async def test_run_tracked_job_records_success(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    result = await run_tracked_job(
        job_type="unit_test",
        idempotency_key="unit_test:once",
        run=lambda: _ok(),
        session_factory=session_factory,
    )
    assert result == {"x": 1}

    async with session_factory() as session:
        job = await session.scalar(
            select(BackgroundJob).where(
                BackgroundJob.idempotency_key == "unit_test:once"
            )
        )
        assert job is not None
        assert job.status == JobStatus.succeeded
        assert job.attempt_count == 1
        assert job.result == {"x": 1}
        assert job.finished_at is not None


async def test_run_tracked_job_records_failure_and_reraises(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    calls = 0

    async def _boom() -> dict[str, int]:
        nonlocal calls
        calls += 1
        raise ValueError("boom")

    try:
        await run_tracked_job(
            job_type="unit_test",
            idempotency_key="unit_test:fails",
            run=_boom,
            session_factory=session_factory,
        )
        raise AssertionError("expected ValueError to propagate")
    except ValueError:
        pass

    assert calls == 1
    async with session_factory() as session:
        job = await session.scalar(
            select(BackgroundJob).where(
                BackgroundJob.idempotency_key == "unit_test:fails"
            )
        )
        assert job is not None
        assert job.status == JobStatus.failed
        assert job.last_error is not None
        assert "boom" in job.last_error


async def test_run_tracked_job_skips_if_already_succeeded(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    calls = 0

    async def _run() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    key = "unit_test:idempotent"
    first = await run_tracked_job(
        job_type="unit_test",
        idempotency_key=key,
        run=_run,
        session_factory=session_factory,
    )
    second = await run_tracked_job(
        job_type="unit_test",
        idempotency_key=key,
        run=_run,
        session_factory=session_factory,
    )
    assert first == {"calls": 1}
    assert second == {"calls": 1}  # cached — _run was not invoked again
    assert calls == 1


async def _ok() -> dict[str, int]:
    return {"x": 1}


async def _seed_cost(
    client: AsyncClient, *, end_date: str | None, status: str | None = None
) -> str:
    ws = (await client.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
    app = (
        await client.post(
            f"/api/v1/workspaces/{ws}/applications", json={"name": "Oído"}
        )
    ).json()["id"]
    vendor = (
        await client.post(f"/api/v1/workspaces/{ws}/vendors", json={"name": "Vercel"})
    ).json()["id"]
    service = (
        await client.post(
            f"/api/v1/workspaces/{ws}/vendors/{vendor}/services", json={"name": "Pro"}
        )
    ).json()["id"]
    payload: dict[str, object] = {
        "application_id": app,
        "service_id": service,
        "name": "Vercel Pro",
        "amount": "20.00",
        "currency": "USD",
        "frequency": "monthly",
    }
    if end_date is not None:
        payload["end_date"] = end_date
    cost = (await client.post(f"/api/v1/workspaces/{ws}/costs", json=payload)).json()
    cost_id = cost["id"]
    if status is not None:
        await client.patch(
            f"/api/v1/workspaces/{ws}/costs/{cost_id}", json={"status": status}
        )
    return cost_id


async def test_auto_end_expired_costs_ends_only_expired_active_costs(
    client_factory: Callable[[], object],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    async with authed_client(client_factory, "owner@example.com") as c:
        expired_active = await _seed_cost(c, end_date=yesterday)
        future_active = await _seed_cost(c, end_date=tomorrow)
        already_ended = await _seed_cost(c, end_date=yesterday, status="ended")

    result = await auto_end_expired_costs({}, session_factory=session_factory)
    assert result == {"ended_count": 1}

    async with session_factory() as session:
        expired = await session.get(CostItem, uuid.UUID(expired_active))
        future = await session.get(CostItem, uuid.UUID(future_active))
        ended = await session.get(CostItem, uuid.UUID(already_ended))
        assert expired is not None and expired.status.value == "ended"
        assert future is not None and future.status.value == "active"
        assert ended is not None and ended.status.value == "ended"

        job = await session.scalar(
            select(BackgroundJob).where(
                BackgroundJob.job_type == "auto_end_expired_costs"
            )
        )
        assert job is not None
        assert job.status == JobStatus.succeeded


async def test_auto_end_expired_costs_is_idempotent_same_day(
    client_factory: Callable[[], object],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    async with authed_client(client_factory, "owner2@example.com") as c:
        await _seed_cost(c, end_date=yesterday)

    first = await auto_end_expired_costs({}, session_factory=session_factory)
    second = await auto_end_expired_costs({}, session_factory=session_factory)
    assert first == {"ended_count": 1}
    assert second == {"ended_count": 1}  # cached from the first run, not re-scanned
