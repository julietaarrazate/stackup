"""Workspace, membership, and cross-workspace isolation tests (ADR-004)."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from tests.conftest import authed_client


async def _create_workspace(client: AsyncClient, name: str = "Oído") -> dict:
    resp = await client.post("/api/v1/workspaces", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_workspace_makes_creator_owner(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "o@example.com", "password": "Sup3rSecret!"},
    )
    await client.post(
        "/api/v1/auth/login",
        data={"username": "o@example.com", "password": "Sup3rSecret!"},
    )
    ws = await _create_workspace(client)
    assert ws["slug"] == "oido"

    resp = await client.get(f"/api/v1/workspaces/{ws['id']}/members")
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"


async def test_slug_is_unique(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "o@example.com", "password": "Sup3rSecret!"},
    )
    await client.post(
        "/api/v1/auth/login",
        data={"username": "o@example.com", "password": "Sup3rSecret!"},
    )
    a = await _create_workspace(client, "Cuadra")
    b = await _create_workspace(client, "Cuadra")
    assert a["slug"] == "cuadra"
    assert b["slug"] != a["slug"]
    assert b["slug"].startswith("cuadra-")


async def test_list_only_returns_my_workspaces(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        await _create_workspace(a, "A-ws")
        async with authed_client(client_factory, "b@example.com") as b:
            await _create_workspace(b, "B-ws")
            resp = await b.get("/api/v1/workspaces")
            assert resp.status_code == 200
            names = [w["name"] for w in resp.json()]
            assert names == ["B-ws"]


async def test_cross_workspace_access_returns_404(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws = await _create_workspace(a, "A-secret")
        async with authed_client(client_factory, "b@example.com") as b:
            # B is not a member of A's workspace -> 404 (existence hidden)
            assert (await b.get(f"/api/v1/workspaces/{ws['id']}")).status_code == 404
            assert (
                await b.patch(f"/api/v1/workspaces/{ws['id']}", json={"name": "hax"})
            ).status_code == 404
            assert (
                await b.get(f"/api/v1/workspaces/{ws['id']}/members")
            ).status_code == 404


async def test_viewer_cannot_update_workspace(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        ws = await _create_workspace(owner, "Shared")
        async with authed_client(client_factory, "viewer@example.com") as viewer:
            # Owner adds viewer
            resp = await owner.post(
                f"/api/v1/workspaces/{ws['id']}/members",
                json={"email": "viewer@example.com", "role": "viewer"},
            )
            assert resp.status_code == 201
            # Viewer can read
            assert (
                await viewer.get(f"/api/v1/workspaces/{ws['id']}")
            ).status_code == 200
            # Viewer cannot update -> 403
            assert (
                await viewer.patch(
                    f"/api/v1/workspaces/{ws['id']}", json={"name": "nope"}
                )
            ).status_code == 403


async def test_member_cannot_manage_members(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        ws = await _create_workspace(owner, "Shared")
        await owner.post(
            "/api/v1/auth/register",
            json={"email": "third@example.com", "password": "Sup3rSecret!"},
        )
        async with authed_client(client_factory, "member@example.com") as member:
            await owner.post(
                f"/api/v1/workspaces/{ws['id']}/members",
                json={"email": "member@example.com", "role": "member"},
            )
            # A member may not add other members -> 403
            resp = await member.post(
                f"/api/v1/workspaces/{ws['id']}/members",
                json={"email": "third@example.com", "role": "member"},
            )
            assert resp.status_code == 403


async def test_admin_cannot_grant_owner(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        ws = await _create_workspace(owner, "Shared")
        await owner.post(
            "/api/v1/auth/register",
            json={"email": "target@example.com", "password": "Sup3rSecret!"},
        )
        async with authed_client(client_factory, "admin@example.com") as admin:
            await owner.post(
                f"/api/v1/workspaces/{ws['id']}/members",
                json={"email": "admin@example.com", "role": "admin"},
            )
            # Admin can add a normal member
            assert (
                await admin.post(
                    f"/api/v1/workspaces/{ws['id']}/members",
                    json={"email": "target@example.com", "role": "member"},
                )
            ).status_code == 201
            # But admin cannot grant the owner role -> 403
            resp = await admin.post(
                f"/api/v1/workspaces/{ws['id']}/members",
                json={"email": "target@example.com", "role": "owner"},
            )
            assert resp.status_code in (403, 409)


async def test_cannot_remove_last_owner(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "o@example.com", "password": "Sup3rSecret!"},
    )
    await client.post(
        "/api/v1/auth/login",
        data={"username": "o@example.com", "password": "Sup3rSecret!"},
    )
    ws = await _create_workspace(client, "Solo")
    members = (await client.get(f"/api/v1/workspaces/{ws['id']}/members")).json()
    owner_member_id = members[0]["id"]
    # Downgrading the only owner is blocked
    resp = await client.patch(
        f"/api/v1/workspaces/{ws['id']}/members/{owner_member_id}",
        json={"role": "admin"},
    )
    assert resp.status_code == 409
    # Removing the only owner is blocked
    resp = await client.delete(
        f"/api/v1/workspaces/{ws['id']}/members/{owner_member_id}"
    )
    assert resp.status_code == 409
