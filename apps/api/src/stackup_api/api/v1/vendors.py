"""Vendor and Service endpoints (Phase 3).

Vendors/services are a shared catalog: a NULL workspace_id is a global entry
visible to everyone; a set workspace_id is private to that workspace. Reads
return global + own rows; writes only ever create/mutate own-workspace rows,
so a workspace can neither see nor modify another's custom vendors.
"""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.db import get_session
from stackup_api.core.deps import WorkspaceContext, get_workspace_context
from stackup_api.core.policy import Action, require
from stackup_api.core.slug import slugify
from stackup_api.models.vendor import Service, Vendor
from stackup_api.schemas.vendor import (
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
    VendorCreate,
    VendorRead,
    VendorUpdate,
)
from stackup_api.services.audit import record_audit

router = APIRouter(prefix="/workspaces/{workspace_id}/vendors", tags=["vendors"])


async def _unique_vendor_slug(
    session: AsyncSession, workspace_id: uuid.UUID, name: str
) -> str:
    base = slugify(name)[:120]
    candidate = base
    while True:
        exists = await session.scalar(
            select(Vendor.id).where(
                Vendor.workspace_id == workspace_id, Vendor.slug == candidate
            )
        )
        if exists is None:
            return candidate
        candidate = f"{base}-{secrets.token_hex(3)}"


async def _get_visible_vendor(
    session: AsyncSession, ctx: WorkspaceContext, vendor_id: uuid.UUID
) -> Vendor:
    """Vendor visible to the workspace (global or own), else 404."""
    vendor = await session.get(Vendor, vendor_id)
    if vendor is None or vendor.workspace_id not in (None, ctx.workspace.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found."
        )
    return vendor


def _require_own_vendor(ctx: WorkspaceContext, vendor: Vendor) -> None:
    """Writes are only allowed on the workspace's own (non-global) vendors."""
    if vendor.workspace_id != ctx.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global catalog vendors cannot be modified by a workspace.",
        )


@router.get("", response_model=list[VendorRead])
async def list_vendors(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[VendorRead]:
    require(ctx.role, Action.DATA_READ)
    stmt = (
        select(Vendor)
        .where(
            or_(
                Vendor.workspace_id.is_(None),
                Vendor.workspace_id == ctx.workspace.id,
            )
        )
        .order_by(Vendor.name)
    )
    vendors = (await session.execute(stmt)).scalars().all()
    return [VendorRead.from_model(v) for v in vendors]


@router.post("", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> VendorRead:
    require(ctx.role, Action.DATA_WRITE)
    vendor = Vendor(
        workspace_id=ctx.workspace.id,
        name=payload.name,
        slug=await _unique_vendor_slug(session, ctx.workspace.id, payload.name),
        website=payload.website,
        logo=payload.logo,
        category=payload.category,
    )
    session.add(vendor)
    await record_audit(
        session,
        actor_user_id=ctx.user.id,
        workspace_id=ctx.workspace.id,
        entity="vendor",
        action="create",
        after={"name": vendor.name, "slug": vendor.slug},
    )
    await session.commit()
    await session.refresh(vendor)
    return VendorRead.from_model(vendor)


@router.get("/{vendor_id}", response_model=VendorRead)
async def get_vendor(
    vendor_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> VendorRead:
    require(ctx.role, Action.DATA_READ)
    vendor = await _get_visible_vendor(session, ctx, vendor_id)
    return VendorRead.from_model(vendor)


@router.patch("/{vendor_id}", response_model=VendorRead)
async def update_vendor(
    vendor_id: uuid.UUID,
    payload: VendorUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> VendorRead:
    require(ctx.role, Action.DATA_WRITE)
    vendor = await _get_visible_vendor(session, ctx, vendor_id)
    _require_own_vendor(ctx, vendor)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vendor, field, value)
    await session.commit()
    await session.refresh(vendor)
    return VendorRead.from_model(vendor)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    vendor = await _get_visible_vendor(session, ctx, vendor_id)
    _require_own_vendor(ctx, vendor)
    await session.delete(vendor)
    await session.commit()


# --- Services (nested under a vendor) ----------------------------------


async def _unique_service_slug(
    session: AsyncSession, vendor_id: uuid.UUID, name: str
) -> str:
    base = slugify(name)[:120]
    candidate = base
    while True:
        exists = await session.scalar(
            select(Service.id).where(
                Service.vendor_id == vendor_id, Service.slug == candidate
            )
        )
        if exists is None:
            return candidate
        candidate = f"{base}-{secrets.token_hex(3)}"


@router.get("/{vendor_id}/services", response_model=list[ServiceRead])
async def list_services(
    vendor_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> list[Service]:
    require(ctx.role, Action.DATA_READ)
    await _get_visible_vendor(session, ctx, vendor_id)
    stmt = select(Service).where(Service.vendor_id == vendor_id).order_by(Service.name)
    return list((await session.execute(stmt)).scalars().all())


@router.post(
    "/{vendor_id}/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    vendor_id: uuid.UUID,
    payload: ServiceCreate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Service:
    require(ctx.role, Action.DATA_WRITE)
    vendor = await _get_visible_vendor(session, ctx, vendor_id)
    # Services may only be added to the workspace's own vendors, never the
    # shared global catalog.
    _require_own_vendor(ctx, vendor)
    service = Service(
        vendor_id=vendor_id,
        name=payload.name,
        slug=await _unique_service_slug(session, vendor_id, payload.name),
        category=payload.category,
        website=payload.website,
    )
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def _get_own_service(
    session: AsyncSession,
    ctx: WorkspaceContext,
    vendor_id: uuid.UUID,
    service_id: uuid.UUID,
) -> Service:
    vendor = await _get_visible_vendor(session, ctx, vendor_id)
    _require_own_vendor(ctx, vendor)
    service = await session.get(Service, service_id)
    if service is None or service.vendor_id != vendor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found."
        )
    return service


@router.patch("/{vendor_id}/services/{service_id}", response_model=ServiceRead)
async def update_service(
    vendor_id: uuid.UUID,
    service_id: uuid.UUID,
    payload: ServiceUpdate,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> Service:
    require(ctx.role, Action.DATA_WRITE)
    service = await _get_own_service(session, ctx, vendor_id, service_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await session.commit()
    await session.refresh(service)
    return service


@router.delete(
    "/{vendor_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_service(
    vendor_id: uuid.UUID,
    service_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    session: AsyncSession = Depends(get_session),
) -> None:
    require(ctx.role, Action.DATA_WRITE)
    service = await _get_own_service(session, ctx, vendor_id, service_id)
    await session.delete(service)
    await session.commit()
