"""Authentication flow tests (register, login, session, logout)."""

from __future__ import annotations

from httpx import AsyncClient

from stackup_api.core.config import get_settings


async def test_register_login_me_logout(client: AsyncClient) -> None:
    email = "user@example.com"
    password = "Sup3rSecret!"

    # Register
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["email"] == email
    assert "hashed_password" not in resp.json()

    # Login sets an HttpOnly session cookie
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 204, resp.text
    cookie_name = get_settings().session_cookie_name
    set_cookie = resp.headers.get("set-cookie", "")
    assert cookie_name in set_cookie
    assert "httponly" in set_cookie.lower()

    # Authenticated request works
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == email

    # Logout revokes the session
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_me_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_wrong_password_rejected(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "password": "Sup3rSecret!"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "a@example.com", "password": "wrong"},
    )
    assert resp.status_code == 400


async def test_register_rate_limited(client: AsyncClient) -> None:
    # register limiter is 5 per hour; the 6th should be blocked
    last_status = None
    for i in range(6):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": f"rl{i}@example.com", "password": "Sup3rSecret!"},
        )
        last_status = resp.status_code
    assert last_status == 429
