"""GitHub integration + detection endpoint tests (Phase 8).

GitHub itself is never called in tests — `services.github_client`'s network
functions are patched, and `core.config.get_settings` is patched wherever a
test needs `github_configured` to be true (test env has no real OAuth app).
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

from stackup_api.core.config import Settings
from tests.conftest import authed_client

_GH_SETTINGS = Settings(
    github_client_id="test-client-id",
    github_client_secret="test-client-secret",
    auth_secret="a-fixed-test-secret-for-signing-state",
)


def _patched_settings():
    return patch(
        "stackup_api.api.v1.integrations.get_settings", return_value=_GH_SETTINGS
    )


async def test_authorize_404_when_github_not_configured(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
        r = await c.get(f"/api/v1/workspaces/{ws}/integrations/github/authorize")
        assert r.status_code == 404


async def test_authorize_returns_signed_state_url(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
        with _patched_settings():
            r = await c.get(f"/api/v1/workspaces/{ws}/integrations/github/authorize")
        assert r.status_code == 200, r.text
        url = r.json()["authorize_url"]
        assert "github.com/login/oauth/authorize" in url
        assert "state=" in url
        assert ws.replace("-", "") in url


async def test_connect_scan_confirm_flow(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
        app = (
            await c.post(f"/api/v1/workspaces/{ws}/applications", json={"name": "Oído"})
        ).json()["id"]
        vendor = (
            await c.post(f"/api/v1/workspaces/{ws}/vendors", json={"name": "Stripe"})
        ).json()["id"]
        service = (
            await c.post(
                f"/api/v1/workspaces/{ws}/vendors/{vendor}/services",
                json={"name": "Billing"},
            )
        ).json()["id"]

        with _patched_settings():
            authorize = await c.get(
                f"/api/v1/workspaces/{ws}/integrations/github/authorize"
            )
            state = authorize.json()["authorize_url"].split("state=")[1]

            with patch(
                "stackup_api.services.github_client.exchange_code_for_token",
                return_value=("gh_fake_token", "octocat"),
            ):
                callback = await c.post(
                    "/api/v1/integrations/github/callback",
                    json={"code": "fake-code", "state": state},
                )
            assert callback.status_code == 200, callback.text
            assert callback.json()["github_login"] == "octocat"

            status_resp = await c.get(f"/api/v1/workspaces/{ws}/integrations/github")
            assert status_resp.status_code == 200
            assert status_resp.json()["github_login"] == "octocat"

            async def _fake_fetch(_token: str, _repo: str, path: str) -> str | None:
                if path == "package.json":
                    return '{"dependencies": {"stripe": "^14.0.0"}}'
                return None

            with patch(
                "stackup_api.services.github_client.fetch_file", side_effect=_fake_fetch
            ):
                scan = await c.post(
                    f"/api/v1/workspaces/{ws}/integrations/github/scan",
                    json={
                        "repo_full_name": "octocat/hello-world",
                        "application_id": app,
                    },
                )
            assert scan.status_code == 200, scan.text
            detections = scan.json()
            assert len(detections) == 1
            assert detections[0]["vendor_name"] == "Stripe"
            assert detections[0]["status"] == "pending"
            detection_id = detections[0]["id"]

        listed = await c.get(
            f"/api/v1/workspaces/{ws}/detections?detection_status=pending"
        )
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        confirm = await c.post(
            f"/api/v1/workspaces/{ws}/detections/{detection_id}/confirm",
            json={
                "application_id": app,
                "service_id": service,
                "name": "Stripe billing",
                "amount": "29.00",
                "currency": "USD",
                "frequency": "monthly",
                "category": "payments",
            },
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["monthly_equivalent"] == "29.00"

        again = await c.post(
            f"/api/v1/workspaces/{ws}/detections/{detection_id}/confirm",
            json={
                "application_id": app,
                "service_id": service,
                "name": "dup",
                "amount": "1.00",
                "currency": "USD",
                "frequency": "monthly",
            },
        )
        assert again.status_code == 409


async def test_scan_requires_connection(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]
        with _patched_settings():
            r = await c.post(
                f"/api/v1/workspaces/{ws}/integrations/github/scan",
                json={"repo_full_name": "octocat/hello-world"},
            )
        assert r.status_code == 404


async def test_dismiss_detection(client_factory: Callable[[], object]) -> None:
    async with authed_client(client_factory, "o@example.com") as c:
        ws = (await c.post("/api/v1/workspaces", json={"name": "Oído"})).json()["id"]

        with _patched_settings():
            authorize = await c.get(
                f"/api/v1/workspaces/{ws}/integrations/github/authorize"
            )
            state = authorize.json()["authorize_url"].split("state=")[1]
            with patch(
                "stackup_api.services.github_client.exchange_code_for_token",
                return_value=("gh_fake_token", "octocat"),
            ):
                await c.post(
                    "/api/v1/integrations/github/callback",
                    json={"code": "fake-code", "state": state},
                )

            async def _fake_fetch(_token: str, _repo: str, path: str) -> str | None:
                return "services:\n  - type: web\n" if path == "render.yaml" else None

            with patch(
                "stackup_api.services.github_client.fetch_file", side_effect=_fake_fetch
            ):
                scan = await c.post(
                    f"/api/v1/workspaces/{ws}/integrations/github/scan",
                    json={"repo_full_name": "octocat/hello-world"},
                )
        detection_id = scan.json()[0]["id"]

        r = await c.post(f"/api/v1/workspaces/{ws}/detections/{detection_id}/dismiss")
        assert r.status_code == 200
        assert r.json()["status"] == "dismissed"


async def test_github_isolated_by_workspace(
    client_factory: Callable[[], object],
) -> None:
    async with authed_client(client_factory, "a@example.com") as a:
        ws_a = (await a.post("/api/v1/workspaces", json={"name": "A"})).json()["id"]
        async with authed_client(client_factory, "b@example.com") as b:
            r = await b.get(f"/api/v1/workspaces/{ws_a}/integrations/github")
            assert r.status_code == 404
            r = await b.get(f"/api/v1/workspaces/{ws_a}/detections")
            assert r.status_code == 404
