"""Slug generation shared across entities."""

from __future__ import annotations

import re
import unicodedata

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Transliterate accents (Oído -> oido) then kebab-case, ASCII-only."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    base = _SLUG_STRIP.sub("-", ascii_only.strip().lower()).strip("-")
    return base or "item"
