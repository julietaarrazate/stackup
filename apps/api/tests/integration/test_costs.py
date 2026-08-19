"""Cost API tests: CRUD, computed values, validation, history, isolation."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from tests.conftest import authed_client


async def _setup(client: AsyncClient) -> dict[str, str]:
    """Create workspace, application, environment, private vendor+service."""
    ws = (await client.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
    app = (
        await client.post(
            f"/api/v1/workspaces/{ws}/applications", json={"name": "Oído"}
        )
    ).json()["id"]
    env = (
        await client.post(
            f"/api/v1/workspaces/{ws}/applications/{app}/environments",
            json={"name": "production", "type": "production"},
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
    return {"ws": ws, "app": app, "env": env, "vendor": vendor, "service": service}


async def test_create_cost_computes_monthly_and_annualized(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        s = await _setup(c)
        resp = await c.post(
            f"/api/v1/workspaces/{s['ws']}/costs",
            json={
                "application_id": s["app"],
                "service_id": s["service"],
                "environment_id": s["env"],
                "name": "Vercel Pro",
                "category": "infrastructure",
                "billing_type": "fixed",
                "amount": "240.00",
                "currency": "usd",
                "frequency": "yearly",
                "certainty": "confirmed",
            },
        )
        assert resp.status_code == 201, resp.text
        cost = resp.json()
        # Amounts are strings (no float on the wire), currency upper-cased.
        assert cost["amount"] == "240.00"
        assert cost["currency"] == "USD"
        assert cost["monthly_equivalent"] == "20.00"
        assert cost["annualized_cost"] == "240.00"


async def test_history_seeded_and_updated_on_price_change(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        s = await _setup(c)
        cost = (
            await c.post(
                f"/api/v1/workspaces/{s['ws']}/costs",
                json={
                    "application_id": s["app"],
                    "service_id": s["service"],
                    "name": "Vercel Pro",
                    "amount": "20.00",
                    "currency": "USD",
                    "frequency": "monthly",
                },
            )
        ).json()

        # Opening history entry exists.
        hist = (
            await c.get(f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}/history")
        ).json()
        assert len(hist) == 1
        assert hist[0]["amount"] == "20.00"
        assert hist[0]["effective_to"] is None

        # Price change appends a new entry and closes the previous one.
        resp = await c.patch(
            f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}",
            json={"amount": "25.00", "change_reason": "Vercel raised prices"},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == "25.00"

        hist = (
            await c.get(f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}/history")
        ).json()
        assert len(hist) == 2
        assert hist[0]["effective_to"] is not None  # previous closed
        assert hist[1]["amount"] == "25.00"
        assert hist[1]["reason"] == "Vercel raised prices"


async def test_amount_must_be_positive(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        s = await _setup(c)
        resp = await c.post(
            f"/api/v1/workspaces/{s['ws']}/costs",
            json={
                "application_id": s["app"],
                "service_id": s["service"],
                "name": "bad",
                "amount": "0",
                "currency": "USD",
                "frequency": "monthly",
            },
        )
        assert resp.status_code == 422


async def test_end_date_before_start_date_rejected(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        s = await _setup(c)
        resp = await c.post(
            f"/api/v1/workspaces/{s['ws']}/costs",
            json={
                "application_id": s["app"],
                "service_id": s["service"],
                "name": "bad dates",
                "amount": "10",
                "currency": "USD",
                "frequency": "monthly",
                "start_date": "2026-06-01",
                "end_date": "2026-01-01",
            },
        )
        assert resp.status_code == 422


async def test_foreign_application_rejected(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        sa = await _setup(a)
        async with authed_client(client_factory, "b@example.com") as b:
            sb = await _setup(b)
            # B tries to attach A's application to a cost in B's workspace.
            resp = await b.post(
                f"/api/v1/workspaces/{sb['ws']}/costs",
                json={
                    "application_id": sa["app"],
                    "service_id": sb["service"],
                    "name": "x",
                    "amount": "10",
                    "currency": "USD",
                    "frequency": "monthly",
                },
            )
            assert resp.status_code == 422


async def test_delete_soft_ends_and_keeps_history(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        s = await _setup(c)
        cost = (
            await c.post(
                f"/api/v1/workspaces/{s['ws']}/costs",
                json={
                    "application_id": s["app"],
                    "service_id": s["service"],
                    "name": "Vercel Pro",
                    "amount": "20.00",
                    "currency": "USD",
                    "frequency": "monthly",
                },
            )
        ).json()
        resp = await c.delete(f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}")
        assert resp.status_code == 204
        got = (await c.get(f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}")).json()
        assert got["status"] == "ended"
        assert got["monthly_equivalent"] == "0.00"  # ended -> no longer recurs
        hist = (
            await c.get(f"/api/v1/workspaces/{s['ws']}/costs/{cost['id']}/history")
        ).json()
        assert len(hist) == 1  # history preserved


async def test_cost_isolation_between_workspaces(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        sa = await _setup(a)
        cost = (
            await a.post(
                f"/api/v1/workspaces/{sa['ws']}/costs",
                json={
                    "application_id": sa["app"],
                    "service_id": sa["service"],
                    "name": "secret",
                    "amount": "10",
                    "currency": "USD",
                    "frequency": "monthly",
                },
            )
        ).json()
        async with authed_client(client_factory, "b@example.com") as b:
            sb = await _setup(b)
            # B cannot read A's cost via B's own workspace path.
            resp = await b.get(f"/api/v1/workspaces/{sb['ws']}/costs/{cost['id']}")
            assert resp.status_code == 404
            # And B is not a member of A's workspace at all -> 404.
            resp = await b.get(f"/api/v1/workspaces/{sa['ws']}/costs/{cost['id']}")
            assert resp.status_code == 404


async def test_viewer_cannot_create_cost(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        s = await _setup(owner)
        async with authed_client(client_factory, "viewer@example.com") as viewer:
            await owner.post(
                f"/api/v1/workspaces/{s['ws']}/members",
                json={"email": "viewer@example.com", "role": "viewer"},
            )
            resp = await viewer.post(
                f"/api/v1/workspaces/{s['ws']}/costs",
                json={
                    "application_id": s["app"],
                    "service_id": s["service"],
                    "name": "x",
                    "amount": "10",
                    "currency": "USD",
                    "frequency": "monthly",
                },
            )
            assert resp.status_code == 403
