"""Report endpoint tests: aggregation, evolution, isolation (Phase 5)."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from tests.conftest import authed_client


async def _setup_with_costs(client: AsyncClient) -> str:
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

    async def add(name: str, amount: str, freq: str, category: str, certainty: str):
        r = await client.post(
            f"/api/v1/workspaces/{ws}/costs",
            json={
                "application_id": app,
                "service_id": service,
                "name": name,
                "amount": amount,
                "currency": "USD",
                "frequency": freq,
                "category": category,
                "certainty": certainty,
            },
        )
        assert r.status_code == 201, r.text

    # 20/mo confirmed infra + 120/yr (=10/mo) estimated software.
    await add("Vercel Pro", "20.00", "monthly", "infrastructure", "confirmed")
    await add("Neon", "120.00", "yearly", "software", "estimated")
    return ws


async def test_overview_totals_and_groups(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _setup_with_costs(c)
        r = await c.get(f"/api/v1/workspaces/{ws}/reports/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["cost_item_count"] == 2
        # Total monthly 20 + 10 = 30 USD; annualized 240 + 120 = 360.
        usd = next(t for t in data["total"] if t["currency"] == "USD")
        assert usd["monthly"] == "30.00"
        assert usd["annualized"] == "360.00"
        # by_certainty
        cert = {
            (x["certainty"], x["currency"]): x["monthly"] for x in data["by_certainty"]
        }
        assert cert[("confirmed", "USD")] == "20.00"
        assert cert[("estimated", "USD")] == "10.00"
        # by_category
        cats = {x["label"]: x["monthly"] for x in data["by_category"]}
        assert cats["infrastructure"] == "20.00"
        assert cats["software"] == "10.00"
        # by_vendor and by_application
        assert data["by_vendor"][0]["label"] == "Vercel"
        assert data["by_application"][0]["label"] == "Oído"
        # recent_changes seeded from the initial history entries
        assert len(data["recent_changes"]) == 2


async def test_evolution_returns_points(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _setup_with_costs(c)
        r = await c.get(f"/api/v1/workspaces/{ws}/reports/evolution?months=3")
        assert r.status_code == 200
        points = r.json()["points"]
        # Current month should reflect the full 30.00 USD monthly total.
        usd_points = [p for p in points if p["currency"] == "USD"]
        assert usd_points
        assert usd_points[-1]["monthly"] == "30.00"


async def test_reports_isolated_by_workspace(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = await _setup_with_costs(a)
        async with authed_client(client_factory, "b@example.com") as b:
            # B is not a member of A's workspace -> 404.
            r = await b.get(f"/api/v1/workspaces/{ws_a}/reports/overview")
            assert r.status_code == 404


async def test_empty_workspace_overview(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Empty"})).json()["id"]
        r = await c.get(f"/api/v1/workspaces/{ws}/reports/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["cost_item_count"] == 0
        assert data["total"] == []
