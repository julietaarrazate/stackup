"""Evidence upload/download/validation + Expense tests (Phase 6)."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

from tests.conftest import authed_client

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def _ws(client: AsyncClient) -> str:
    return (await client.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]


async def test_upload_download_delete_evidence(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        # Upload a small PNG as a receipt.
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/evidence",
            files={"file": ("factura.png", PNG, "image/png")},
            data={"type": "receipt"},
        )
        assert resp.status_code == 201, resp.text
        ev = resp.json()
        assert ev["filename"] == "factura.png"
        assert ev["mime_type"] == "image/png"
        assert ev["size"] == len(PNG)
        assert "storage_key" not in ev  # storage key never exposed

        # Download returns the exact bytes through the authorized endpoint.
        resp = await c.get(f"/api/v1/workspaces/{ws}/evidence/{ev['id']}/download")
        assert resp.status_code == 200
        assert resp.content == PNG
        assert "attachment" in resp.headers["content-disposition"]

        # List + delete.
        assert len((await c.get(f"/api/v1/workspaces/{ws}/evidence")).json()) == 1
        assert (
            await c.delete(f"/api/v1/workspaces/{ws}/evidence/{ev['id']}")
        ).status_code == 204


async def test_reject_disallowed_mime(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/evidence",
            files={"file": ("evil.exe", b"MZ...", "application/x-msdownload")},
            data={"type": "other"},
        )
        assert resp.status_code == 422


async def test_evidence_isolation(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = await _ws(a)
        ev = (
            await a.post(
                f"/api/v1/workspaces/{ws_a}/evidence",
                files={"file": ("a.png", PNG, "image/png")},
                data={"type": "invoice"},
            )
        ).json()
        async with authed_client(client_factory, "b@example.com") as b:
            # B cannot download A's evidence through A's workspace (not a member).
            resp = await b.get(
                f"/api/v1/workspaces/{ws_a}/evidence/{ev['id']}/download"
            )
            assert resp.status_code == 404


async def test_viewer_cannot_upload(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "owner@example.com") as owner:
        ws = await _ws(owner)
        async with authed_client(client_factory, "viewer@example.com") as viewer:
            await owner.post(
                f"/api/v1/workspaces/{ws}/members",
                json={"email": "viewer@example.com", "role": "viewer"},
            )
            resp = await viewer.post(
                f"/api/v1/workspaces/{ws}/evidence",
                files={"file": ("a.png", PNG, "image/png")},
                data={"type": "invoice"},
            )
            assert resp.status_code == 403


async def _setup_cost(client: AsyncClient, ws: str) -> str:
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
    cost = (
        await client.post(
            f"/api/v1/workspaces/{ws}/costs",
            json={
                "application_id": app,
                "service_id": service,
                "name": "Vercel Pro",
                "amount": "20.00",
                "currency": "USD",
                "frequency": "monthly",
            },
        )
    ).json()["id"]
    return cost


async def test_expense_with_evidence(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = await _ws(c)
        cost = await _setup_cost(c, ws)
        ev = (
            await c.post(
                f"/api/v1/workspaces/{ws}/evidence",
                files={"file": ("aug.png", PNG, "image/png")},
                data={"type": "invoice"},
            )
        ).json()
        resp = await c.post(
            f"/api/v1/workspaces/{ws}/expenses",
            json={
                "cost_item_id": cost,
                "amount": "20.00",
                "currency": "USD",
                "paid_at": "2026-08-01",
                "status": "paid",
                "invoice_number": "INV-1",
                "evidence_id": ev["id"],
            },
        )
        assert resp.status_code == 201, resp.text
        exp = resp.json()
        assert exp["amount"] == "20.00"
        assert exp["evidence_id"] == ev["id"]

        # List by cost item.
        listed = (
            await c.get(f"/api/v1/workspaces/{ws}/expenses?cost_item_id={cost}")
        ).json()
        assert len(listed) == 1


async def test_expense_foreign_cost_rejected(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = await _ws(a)
        cost_a = await _setup_cost(a, ws_a)
        async with authed_client(client_factory, "b@example.com") as b:
            ws_b = await _ws(b)
            resp = await b.post(
                f"/api/v1/workspaces/{ws_b}/expenses",
                json={
                    "cost_item_id": cost_a,
                    "amount": "20.00",
                    "currency": "USD",
                },
            )
            assert resp.status_code == 422
