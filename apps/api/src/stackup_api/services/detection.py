"""Cost-signal detection heuristics (Phase 8).

Pure functions: given a manifest file's path and text content, return zero or
more `DetectionCandidate`s. Never touches the network or the database — the
API layer fetches files via `github_client` and persists what this module
finds as `Detection` rows (status=pending). Nothing here ever creates a
CostItem.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from stackup_api.models.enums import DetectionConfidence

# Known manifest files worth fetching from a repo, in fetch order.
KNOWN_MANIFEST_FILES: list[str] = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "render.yaml",
    "vercel.json",
    "fly.toml",
    "Procfile",
    "docker-compose.yml",
    "docker-compose.yaml",
]


@dataclass(frozen=True)
class DetectionCandidate:
    vendor_name: str
    category: str
    evidence: str
    confidence: DetectionConfidence


# package name (npm) -> (vendor, category)
_NPM_SIGNALS: dict[str, tuple[str, str]] = {
    "stripe": ("Stripe", "payments"),
    "resend": ("Resend", "email"),
    "openai": ("OpenAI", "ai"),
    "@upstash/redis": ("Upstash", "infrastructure"),
    "twilio": ("Twilio", "communications"),
    "posthog-js": ("PostHog", "analytics"),
    "posthog-node": ("PostHog", "analytics"),
    "@neondatabase/serverless": ("Neon", "database"),
    "algoliasearch": ("Algolia", "search"),
    "cloudinary": ("Cloudinary", "media"),
    "mixpanel-browser": ("Mixpanel", "analytics"),
    "@clerk/nextjs": ("Clerk", "auth"),
    "@clerk/clerk-react": ("Clerk", "auth"),
    "@auth0/auth0-react": ("Auth0", "auth"),
    "@supabase/supabase-js": ("Supabase", "database"),
}
_NPM_PREFIX_SIGNALS: dict[str, tuple[str, str]] = {
    "@sentry/": ("Sentry", "observability"),
    "@aws-sdk/": ("AWS", "infrastructure"),
}

# package name (pip) -> (vendor, category)
_PY_SIGNALS: dict[str, tuple[str, str]] = {
    "stripe": ("Stripe", "payments"),
    "boto3": ("AWS", "infrastructure"),
    "sentry-sdk": ("Sentry", "observability"),
    "openai": ("OpenAI", "ai"),
    "twilio": ("Twilio", "communications"),
    "asyncpg": ("PostgreSQL", "database"),
    "psycopg2": ("PostgreSQL", "database"),
    "psycopg2-binary": ("PostgreSQL", "database"),
    "psycopg": ("PostgreSQL", "database"),
    "redis": ("Redis", "infrastructure"),
    "resend": ("Resend", "email"),
}

# file basename -> (vendor, category) — presence alone is the signal.
_FILE_PRESENCE_SIGNALS: dict[str, tuple[str, str]] = {
    "render.yaml": ("Render", "hosting"),
    "vercel.json": ("Vercel", "hosting"),
    "fly.toml": ("Fly.io", "hosting"),
    "Procfile": ("Heroku", "hosting"),
}

# docker-compose service image -> (vendor, category)
_COMPOSE_IMAGE_SIGNALS: dict[str, tuple[str, str]] = {
    "postgres": ("PostgreSQL", "database"),
    "redis": ("Redis", "infrastructure"),
    "mysql": ("MySQL", "database"),
    "mongo": ("MongoDB", "database"),
    "rabbitmq": ("RabbitMQ", "infrastructure"),
    "elasticsearch": ("Elasticsearch", "infrastructure"),
}


def scan_file(file_path: str, content: str) -> list[DetectionCandidate]:
    name = file_path.rsplit("/", 1)[-1]
    if name == "package.json":
        return _scan_package_json(content)
    if name == "requirements.txt":
        return _scan_requirements_txt(content)
    if name == "pyproject.toml":
        return _scan_text_for_signals(content, _PY_SIGNALS, DetectionConfidence.medium)
    if name in ("docker-compose.yml", "docker-compose.yaml"):
        return _scan_compose(content)
    if name in _FILE_PRESENCE_SIGNALS:
        vendor, category = _FILE_PRESENCE_SIGNALS[name]
        return [
            DetectionCandidate(
                vendor_name=vendor,
                category=category,
                evidence=f"{name} present in repo",
                confidence=DetectionConfidence.high,
            )
        ]
    return []


def _scan_package_json(content: str) -> list[DetectionCandidate]:
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return []
    deps: dict[str, str] = {
        **data.get("dependencies", {}),
        **data.get("devDependencies", {}),
    }
    candidates: list[DetectionCandidate] = []
    for pkg, version in deps.items():
        if pkg in _NPM_SIGNALS:
            vendor, category = _NPM_SIGNALS[pkg]
            candidates.append(
                DetectionCandidate(
                    vendor_name=vendor,
                    category=category,
                    evidence=f'"{pkg}": "{version}" in package.json',
                    confidence=DetectionConfidence.high,
                )
            )
            continue
        for prefix, (vendor, category) in _NPM_PREFIX_SIGNALS.items():
            if pkg.startswith(prefix):
                candidates.append(
                    DetectionCandidate(
                        vendor_name=vendor,
                        category=category,
                        evidence=f'"{pkg}": "{version}" in package.json',
                        confidence=DetectionConfidence.high,
                    )
                )
                break
    return candidates


def _scan_requirements_txt(content: str) -> list[DetectionCandidate]:
    candidates: list[DetectionCandidate] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)", line)
        if not match:
            continue
        pkg = match.group(1).lower()
        if pkg in _PY_SIGNALS:
            vendor, category = _PY_SIGNALS[pkg]
            candidates.append(
                DetectionCandidate(
                    vendor_name=vendor,
                    category=category,
                    evidence=f"{line} in requirements.txt",
                    confidence=DetectionConfidence.high,
                )
            )
    return candidates


def _scan_text_for_signals(
    content: str, signals: dict[str, tuple[str, str]], confidence: DetectionConfidence
) -> list[DetectionCandidate]:
    candidates: list[DetectionCandidate] = []
    for pkg, (vendor, category) in signals.items():
        if re.search(rf'["\']{re.escape(pkg)}(?=[><=!,"\']|\s)', content):
            candidates.append(
                DetectionCandidate(
                    vendor_name=vendor,
                    category=category,
                    evidence=f"{pkg} referenced in pyproject.toml",
                    confidence=confidence,
                )
            )
    return candidates


def _scan_compose(content: str) -> list[DetectionCandidate]:
    candidates: list[DetectionCandidate] = []
    for image, (vendor, category) in _COMPOSE_IMAGE_SIGNALS.items():
        match = re.search(rf"image:\s*[\"']?({re.escape(image)}[\w:.-]*)", content)
        if match:
            candidates.append(
                DetectionCandidate(
                    vendor_name=vendor,
                    category=category,
                    evidence=f"image: {match.group(1)} in docker-compose",
                    confidence=DetectionConfidence.medium,
                )
            )
    return candidates
