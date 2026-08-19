"""Development/test data seeding (docs section 33).

Two independent parts:

- `seed_catalog`: the shared global vendor/service catalog (real reference
  data: Vercel, Neon, Render, ...). Idempotent by slug.
- `seed_examples`: the Oído / Cuadra / Stackup example workspaces with a demo
  user, applications and environments — clearly development-only.

Running against a production ENVIRONMENT is refused outright: seed data must
never land in production (docs sections 33, 41).

Usage:
    uv run python -m stackup_api.seed            # catalog only
    uv run python -m stackup_api.seed --examples # catalog + examples
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.config import get_settings
from stackup_api.core.db import SessionLocal
from stackup_api.core.slug import slugify
from stackup_api.models.application import Application, Environment
from stackup_api.models.enums import ApplicationStatus, EnvironmentType, WorkspaceRole
from stackup_api.models.user import User
from stackup_api.models.vendor import Service, Vendor
from stackup_api.models.workspace import Workspace, WorkspaceMember

# Global catalog: (name, category, website, [service names])
CATALOG: list[tuple[str, str, str, list[str]]] = [
    ("Vercel", "infrastructure", "https://vercel.com", ["Hobby", "Pro", "Enterprise"]),
    ("Neon", "infrastructure", "https://neon.com", ["Free", "Launch", "Scale"]),
    ("Render", "infrastructure", "https://render.com", ["Free", "Starter", "Standard"]),
    ("Cloudflare", "infrastructure", "https://cloudflare.com", ["Free", "Pro", "R2"]),
    ("Upstash", "infrastructure", "https://upstash.com", ["Free", "Pay as you go"]),
    ("Sentry", "software", "https://sentry.io", ["Developer", "Team", "Business"]),
    ("GitHub", "software", "https://github.com", ["Free", "Team", "Enterprise"]),
    ("Resend", "apis", "https://resend.com", ["Free", "Pro"]),
    ("Cloudinary", "apis", "https://cloudinary.com", ["Free", "Plus", "Advanced"]),
]


async def seed_catalog(session: AsyncSession) -> int:
    """Insert any missing global (workspace_id NULL) vendors + services."""
    created = 0
    for name, category, website, services in CATALOG:
        slug = slugify(name)
        vendor = await session.scalar(
            select(Vendor).where(Vendor.workspace_id.is_(None), Vendor.slug == slug)
        )
        if vendor is None:
            vendor = Vendor(
                workspace_id=None,
                name=name,
                slug=slug,
                website=website,
                category=category,
            )
            session.add(vendor)
            await session.flush()
            created += 1
        existing = {
            s.slug
            for s in (
                await session.execute(
                    select(Service).where(Service.vendor_id == vendor.id)
                )
            ).scalars()
        }
        for svc_name in services:
            svc_slug = slugify(svc_name)
            if svc_slug not in existing:
                session.add(
                    Service(
                        vendor_id=vendor.id,
                        name=svc_name,
                        slug=svc_slug,
                        category=category,
                    )
                )
    await session.commit()
    return created


async def seed_examples(session: AsyncSession) -> None:
    """Seed the Oído / Cuadra / Stackup example workspaces (dev only)."""
    demo_email = "demo@stackup.dev"
    user = await session.scalar(
        select(User).where(func.lower(User.email) == demo_email)
    )
    if user is None:
        # Password hashing goes through the user manager in real flows; for the
        # dev seed we set a known bcrypt-able password via fastapi-users helper.
        from fastapi_users.password import PasswordHelper

        user = User(
            email=demo_email,
            hashed_password=PasswordHelper().hash("Demo12345!"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()

    examples = {
        "Oído": ["production", "staging", "development"],
        "Cuadra": ["production", "staging"],
        "Stackup": ["production"],
    }
    for ws_name, envs in examples.items():
        slug = slugify(ws_name)
        ws = await session.scalar(select(Workspace).where(Workspace.slug == slug))
        if ws is not None:
            continue
        ws = Workspace(name=ws_name, slug=slug, base_currency="USD", timezone="UTC")
        session.add(ws)
        await session.flush()
        session.add(
            WorkspaceMember(
                workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.owner
            )
        )
        app = Application(
            workspace_id=ws.id,
            name=ws_name,
            slug=slug,
            status=ApplicationStatus.active,
        )
        session.add(app)
        await session.flush()
        for env_name in envs:
            session.add(
                Environment(
                    application_id=app.id,
                    name=env_name,
                    type=EnvironmentType(env_name)
                    if env_name in EnvironmentType.__members__
                    else EnvironmentType.other,
                )
            )
    await session.commit()


async def main(*, with_examples: bool) -> None:
    settings = get_settings()
    if settings.is_production:
        raise SystemExit("Refusing to seed a production environment (docs §33/§41).")
    async with SessionLocal() as session:
        created = await seed_catalog(session)
        print(f"catalog: {created} new vendors seeded")
        if with_examples:
            await seed_examples(session)
            print("examples: Oído / Cuadra / Stackup seeded (dev only)")


if __name__ == "__main__":
    asyncio.run(main(with_examples="--examples" in sys.argv))
