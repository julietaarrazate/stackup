"""Application + Environment CRUD and isolation tests (Phase 3)."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from tests.conftest import authed_client


async def _ws(client: AsyncClient, name: str = "Oído") -> str:
    resp = await client.post("/api/v1/workspaces", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_application_crud(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        # Create
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/applications",
            json={"name": "Oído", "repository_url": "https://github.com/x/oido"},
        )
        assert resp.status_code == 201, resp.text
        app = resp.json()
        assert app["slug"] == "oido"
        assert app["status"] == "active"

        # List
        resp = await c.get(f"/api/v1/workspaces/{ws}/applications")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Get
        resp = await c.get(f"/api/v1/workspaces/{ws}/applications/{app['id']}")
        assert resp.status_code == 200

        # Archive via PATCH
        resp = await c.patch(
            f"/api/v1/workspaces/{ws}/applications/{app['id']}",
            json={"status": "archived"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

        # Filter by status
        resp = await c.get(f"/api/v1/workspaces/{ws}/applications?status_filter=active")
        assert resp.json() == []

        # Delete
        resp = await c.delete(f"/api/v1/workspaces/{ws}/applications/{app['id']}")
        assert resp.status_code == 204


async def test_environments_crud(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        app = (
            await c.post(f"/api/v1/workspaces/{ws}/applications", json={"name": "Oído"})
        ).json()
        # Create environments
        for env in ("production", "staging", "development"):
            resp = await c.post(
                f"/api/v1/workspaces/{ws}/applications/{app['id']}/environments",
                json={"name": env, "type": env},
            )
            assert resp.status_code == 201, resp.text
        resp = await c.get(
            f"/api/v1/workspaces/{ws}/applications/{app['id']}/environments"
        )
        assert len(resp.json()) == 3

        # Duplicate environment name is rejected by the unique constraint
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/applications/{app['id']}/environments",
            json={"name": "production", "type": "production"},
        )
        assert resp.status_code >= 400


async def test_application_isolation(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = await _ws(a, "A")
        app = (
            await a.post(
                f"/api/v1/workspaces/{ws_a}/applications", json={"name": "Secret"}
            )
        ).json()
        async with authed_client(client_factory, "b@example.com") as b:
            # B cannot see A's workspace applications -> 404 on the workspace
            assert (
                await b.get(f"/api/v1/workspaces/{ws_a}/applications")
            ).status_code == 404
            assert (
                await b.get(f"/api/v1/workspaces/{ws_a}/applications/{app['id']}")
            ).status_code == 404


async def test_viewer_cannot_create_application(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        ws = await _ws(owner, "Shared")
        async with authed_client(client_factory, "viewer@example.com") as viewer:
            await owner.post(
                f"/api/v1/workspaces/{ws}/members",
                json={"email": "viewer@example.com", "role": "viewer"},
            )
            resp = await viewer.post(
                f"/api/v1/workspaces/{ws}/applications", json={"name": "X"}
            )
            assert resp.status_code == 403
