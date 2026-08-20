"""GitHub integration endpoints (Phase 8).

Connect/disconnect/list-repos/scan are nested under the workspace like every
other resource. The OAuth callback is the one exception: GitHub redirects to
a single fixed URL with no workspace id in the path, so it lives at the
top level and recovers the workspace from the signed `state` param —
re-verifying real membership + permission before trusting it.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.config import get_settings
from stackup_api.core.crypto import decrypt_secret, encrypt_secret
from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.core.users import current_active_user
from stackup_api.models.application import Application
from stackup_api.models.enums import DetectionStatus
from stackup_api.models.integration import Detection, GitHubConnection
from stackup_api.models.user import User
from stackup_api.models.workspace import Workspace, WorkspaceMember
from stackup_api.schemas.integration import (
    DetectionRead,
    GitHubAuthorizeResponse,
    GitHubCallback,
    GitHubConnectionRead,
    GitHubRepo,
    ScanRequest,
)
from stackup_api.services import github_client
from stackup_api.services.detection import KNOWN_MANIFEST_FILES, scan_file

router = APIRouter(
    prefix="/workspaces/{workspace_id}/integrations/github", tags=["integrations"]
)
callback_router = APIRouter(prefix="/integrations/github", tags=["integrations"])


def _require_github_configured() -> None:
    if not get_settings().github_configured:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub integration is not configured on this server.",
        )


async def _get_connection(
    session: AsyncSession, workspace_id: uuid.UUID
) -> GitHubConnection | None:
    return await session.scalar(  # type: ignore[no-any-return]
        select(GitHubConnection).where(GitHubConnection.workspace_id == workspace_id)
    )


@router.get("/authorize", response_model=GitHubAuthorizeResponse)
async def authorize(
    ctx: WorkspaceContext = Depends(get_workspace_context),
) -> GitHubAuthorizeResponse:
    _require_github_configured()
    require(ctx.role, Action.WORKSPACE_UPDATE)
    state = github_client.sign_state(
        ctx.workspace.id, auth_secret=get_settings().auth_secret
    )
    return GitHubAuthorizeResponse(
        authorize_url=github_client.authorize_url(state=state)
    )


@callback_router.post("/callback", response_model=GitHubConnectionRead)
async def callback(
    payload: GitHubCallback,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
) -> GitHubConnectionRead:
    _require_github_configured()
    settings = get_settings()
    try:
        workspace_id = github_client.verify_state(
            payload.state, auth_secret=settings.auth_secret
        )
    except github_client.GitHubAPIError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    row = (
        await session.execute(
            select(Workspace, WorkspaceMember)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(Workspace.id == workspace_id, WorkspaceMember.user_id == user.id)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found.")
    _workspace, membership = row
    require(membership.role, Action.WORKSPACE_UPDATE)

    try:
        access_token, github_login = await github_client.exchange_code_for_token(
            payload.code
        )
    except github_client.GitHubAPIError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    encrypted = encrypt_secret(access_token, auth_secret=settings.auth_secret)
    connection = await _get_connection(session, workspace_id)
    if connection is None:
        connection = GitHubConnection(
            workspace_id=workspace_id,
            github_login=github_login,
            access_token_encrypted=encrypted,
        )
        session.add(connection)
    else:
        connection.github_login = github_login
        connection.access_token_encrypted = encrypted
    await session.commit()
    await session.refresh(connection)
    return GitHubConnectionRead.model_validate(connection)


@router.get("", response_model=GitHubConnectionRead)
async def get_connection(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> GitHubConnectionRead:
    require(ctx.role, Action.DATA_READ)
    connection = await _get_connection(session, ctx.workspace.id)
    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not connected.")
    return GitHubConnectionRead.model_validate(connection)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.WORKSPACE_UPDATE)
    connection = await _get_connection(session, ctx.workspace.id)
    if connection is not None:
        await session.delete(connection)
        await session.commit()


async def _connected_token(session: AsyncSession, ctx: WorkspaceContext) -> str:
    connection = await _get_connection(session, ctx.workspace.id)
    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "GitHub is not connected.")
    return decrypt_secret(
        connection.access_token_encrypted, auth_secret=get_settings().auth_secret
    )


@router.get("/repos", response_model=list[GitHubRepo])
async def repos(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[GitHubRepo]:
    require(ctx.role, Action.DATA_READ)
    token = await _connected_token(session, ctx)
    try:
        data = await github_client.list_repos(token)
    except github_client.GitHubAPIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    return [GitHubRepo.model_validate(r) for r in data]


@router.post("/scan", response_model=list[DetectionRead])
async def scan(
    payload: ScanRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[DetectionRead]:
    require(ctx.role, Action.DATA_WRITE)
    if payload.application_id is not None:
        app = await session.get(Application, payload.application_id)
        if app is None or app.workspace_id != ctx.workspace.id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "application_id does not belong to this workspace.",
            )
    token = await _connected_token(session, ctx)

    found: list[Detection] = []
    for path in KNOWN_MANIFEST_FILES:
        try:
            content = await github_client.fetch_file(
                token, payload.repo_full_name, path
            )
        except github_client.GitHubAPIError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
        if content is None:
            continue
        for candidate in scan_file(path, content):
            existing = await session.scalar(
                select(Detection).where(
                    Detection.workspace_id == ctx.workspace.id,
                    Detection.repo_full_name == payload.repo_full_name,
                    Detection.file_path == path,
                    Detection.vendor_name == candidate.vendor_name,
                )
            )
            if existing is not None:
                # Rescan refreshes the evidence but never resets a decision
                # the user already made.
                existing.evidence = candidate.evidence
                existing.confidence = candidate.confidence
                found.append(existing)
                continue
            detection = Detection(
                workspace_id=ctx.workspace.id,
                application_id=payload.application_id,
                repo_full_name=payload.repo_full_name,
                file_path=path,
                vendor_name=candidate.vendor_name,
                category=candidate.category,
                evidence=candidate.evidence,
                confidence=candidate.confidence,
                status=DetectionStatus.pending,
            )
            session.add(detection)
            found.append(detection)

    await session.commit()
    for d in found:
        await session.refresh(d)
    return [DetectionRead.model_validate(d) for d in found]
