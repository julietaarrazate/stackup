"""Thin GitHub REST API client (Phase 8).

Only what the detection flow needs: exchange an OAuth code, list the
connected account's repos, and fetch a single file's contents. No webhook or
GitHub App machinery — an OAuth App with the `repo` scope is enough for
read-only manifest scanning.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid

import httpx

from stackup_api.core.config import get_settings

_GITHUB_API = "https://api.github.com"
_GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"


class GitHubAPIError(RuntimeError):
    pass


def sign_state(workspace_id: uuid.UUID, *, auth_secret: str) -> str:
    """A tamper-evident `state` param carrying which workspace is connecting.

    GitHub's OAuth callback is a single fixed URL with no room for a
    workspace id in the path, so it has to travel round-trip in `state`.
    The signature only guards integrity; the callback still re-checks real
    workspace membership + permission before trusting it.
    """
    payload = workspace_id.hex
    sig = hmac.new(auth_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_state(state: str, *, auth_secret: str) -> uuid.UUID:
    try:
        payload, sig = state.split(".", 1)
    except ValueError as exc:
        raise GitHubAPIError("Invalid OAuth state.") from exc
    expected = hmac.new(
        auth_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise GitHubAPIError("Invalid OAuth state.")
    try:
        return uuid.UUID(payload)
    except ValueError as exc:
        raise GitHubAPIError("Invalid OAuth state.") from exc


def authorize_url(*, state: str) -> str:
    settings = get_settings()
    params = (
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        "&scope=repo"
        f"&state={state}"
    )
    return f"https://github.com/login/oauth/authorize?{params}"


async def exchange_code_for_token(code: str) -> tuple[str, str]:
    """(access_token, github_login) for the OAuth-authorized account."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            _GITHUB_OAUTH_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise GitHubAPIError(
                token_data.get("error_description", "GitHub token exchange failed.")
            )

        user_resp = await client.get(
            f"{_GITHUB_API}/user",
            headers=_auth_headers(access_token),
        )
        if user_resp.status_code >= 400:
            raise GitHubAPIError("Could not read the GitHub account after connecting.")
        return access_token, user_resp.json()["login"]


async def list_repos(access_token: str) -> list[dict[str, object]]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{_GITHUB_API}/user/repos",
            headers=_auth_headers(access_token),
            params={"per_page": 100, "sort": "pushed"},
        )
    if resp.status_code >= 400:
        raise GitHubAPIError("Could not list GitHub repositories.")
    return [
        {
            "full_name": r["full_name"],
            "private": r["private"],
            "default_branch": r["default_branch"],
        }
        for r in resp.json()
    ]


async def fetch_file(access_token: str, repo_full_name: str, path: str) -> str | None:
    """The file's text content, or None if it doesn't exist in the repo."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{_GITHUB_API}/repos/{repo_full_name}/contents/{path}",
            headers=_auth_headers(access_token),
        )
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise GitHubAPIError(f"Could not fetch {path} from {repo_full_name}.")
    data = resp.json()
    if data.get("encoding") != "base64":
        return None
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
