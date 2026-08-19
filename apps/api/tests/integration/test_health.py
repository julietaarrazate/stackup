"""Health, readiness, and API-mount smoke tests."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_does_not_leak_details(client: AsyncClient) -> None:
    resp = await client.get("/health")
    # Liveness must expose only a status — nothing else.
    assert set(resp.json().keys()) == {"status"}


async def test_ready_reports_database(client: AsyncClient) -> None:
    resp = await client.get("/ready")
    body = resp.json()
    assert "database" in body["checks"]
    # Readiness returns only statuses, never the underlying reason/DSN.
    assert body["checks"]["database"] in {"ok", "unavailable"}


async def test_request_id_header_present(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("X-Request-Id")


async def test_request_id_is_echoed_when_supplied(client: AsyncClient) -> None:
    resp = await client.get("/health", headers={"X-Request-Id": "abc123"})
    assert resp.headers.get("X-Request-Id") == "abc123"


async def test_api_v1_meta(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/meta")
    assert resp.status_code == 200
    assert resp.json() == {"api": "stackup", "version": "v1"}
