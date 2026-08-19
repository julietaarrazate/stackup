"""Vendor + Service catalog, scope, and isolation tests (Phase 3)."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from stackup_api.core.db import Base
from stackup_api.seed import seed_catalog
from tests.conftest import authed_client


async def _ws(client: AsyncClient, name: str = "WS") -> str:
    resp = await client.post("/api/v1/workspaces", json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_private_vendor_and_service_crud(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        # Create a private vendor
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/vendors",
            json={"name": "Mi Proveedor", "category": "apis"},
        )
        assert resp.status_code == 201, resp.text
        vendor = resp.json()
        assert vendor["is_global"] is False
        assert vendor["slug"] == "mi-proveedor"

        # Add a service to it
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/vendors/{vendor['id']}/services",
            json={"name": "Plan Pro"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["slug"] == "plan-pro"

        # List services
        resp = await c.get(f"/api/v1/workspaces/{ws}/vendors/{vendor['id']}/services")
        assert len(resp.json()) == 1


async def test_global_catalog_visible_but_not_writable(
    client_factory: Callable[[], object],
    session_factory,
) -> None:
    # Seed the global catalog into the shared test DB.
    async with session_factory() as session:
        await seed_catalog(session)

    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        resp = await c.get(f"/api/v1/workspaces/{ws}/vendors")
        assert resp.status_code == 200
        vendors = resp.json()
        names = {v["name"] for v in vendors}
        assert "Vercel" in names and "Neon" in names
        global_vendor = next(v for v in vendors if v["name"] == "Vercel")
        assert global_vendor["is_global"] is True

        # A workspace cannot modify a global catalog vendor -> 403
        resp = await c.patch(
            f"/api/v1/workspaces/{ws}/vendors/{global_vendor['id']}",
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403
        # Nor add services to it
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/vendors/{global_vendor['id']}/services",
            json={"name": "X"},
        )
        assert resp.status_code == 403


async def test_private_vendor_not_visible_to_other_workspace(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = await _ws(a, "A")
        vendor = (
            await a.post(
                f"/api/v1/workspaces/{ws_a}/vendors", json={"name": "Privado A"}
            )
        ).json()
        async with authed_client(client_factory, "b@example.com") as b:
            ws_b = await _ws(b, "B")
            # B's vendor list must not include A's private vendor
            resp = await b.get(f"/api/v1/workspaces/{ws_b}/vendors")
            assert all(v["name"] != "Privado A" for v in resp.json())
            # And B cannot fetch it directly through B's workspace -> 404
            resp = await b.get(f"/api/v1/workspaces/{ws_b}/vendors/{vendor['id']}")
            assert resp.status_code == 404


def test_base_metadata_has_phase3_tables() -> None:
    for table in ("application", "environment", "vendor", "service"):
        assert table in Base.metadata.tables
