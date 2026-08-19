"""Evidence endpoints (Phase 6, ADR-006).

Uploads are validated server-side (MIME/extension/size); the object is stored
under a random key (never the user filename) in private object storage.
Downloads stream through this authorized endpoint — evidence is never served
from a public URL.
"""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.config import get_settings
from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.models.enums import EvidenceType
from stackup_api.models.evidence import Evidence
from stackup_api.schemas.evidence import EvidenceRead
from stackup_api.services.audit import record_audit
from stackup_api.storage import get_storage
from stackup_api.storage.factory import (
    UploadValidationError,
    build_storage_key,
    validate_upload,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/evidence", tags=["evidence"])


async def _get_evidence(
    session: AsyncSession, ctx: WorkspaceContext, evidence_id: uuid.UUID
) -> Evidence:
    ev = await session.get(Evidence, evidence_id)
    if ev is None or ev.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found."
        )
    return ev


@router.post("", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    type: EvidenceType = Form(EvidenceType.invoice),
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Evidence:
    require(ctx.role, Action.DATA_WRITE)
    settings = get_settings()
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    try:
        validate_upload(
            content_type=content_type,
            size=len(data),
            max_mb=settings.max_upload_size_mb,
        )
    except UploadValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    key = build_storage_key(ctx.workspace.id, content_type)
    await get_storage().put(key, data, content_type)

    evidence = Evidence(
        workspace_id=ctx.workspace.id,
        type=type,
        # The client filename is metadata only — sanitized to its basename and
        # never used as a storage path.
        filename=(file.filename or "archivo").rsplit("/", 1)[-1][:255],
        storage_key=key,
        mime_type=content_type,
        size=len(data),
    )
    session.add(evidence)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="evidence",
        action="upload",
        after={"filename": evidence.filename, "size": evidence.size},
    )
    await session.commit()
    await session.refresh(evidence)
    return evidence


@router.get("", response_model=list[EvidenceRead])
async def list_evidence(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[Evidence]:
    require(ctx.role, Action.DATA_READ)
    stmt = (
        select(Evidence)
        .where(Evidence.workspace_id == ctx.workspace.id)
        .order_by(Evidence.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


@router.get("/{evidence_id}", response_model=EvidenceRead)
async def get_evidence(
    evidence_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Evidence:
    require(ctx.role, Action.DATA_READ)
    return await _get_evidence(session, ctx, evidence_id)


@router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Response:
    require(ctx.role, Action.DATA_READ)
    ev = await _get_evidence(session, ctx, evidence_id)
    try:
        data = await get_storage().get(ev.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File is missing."
        ) from exc
    return Response(
        content=data,
        media_type=ev.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{ev.filename}"',
            # Private, never cached by shared caches.
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    ev = await _get_evidence(session, ctx, evidence_id)
    await get_storage().delete(ev.storage_key)
    await session.delete(ev)
    await session.commit()
