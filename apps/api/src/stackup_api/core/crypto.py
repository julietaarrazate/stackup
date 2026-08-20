"""Symmetric encryption for secrets stored at rest (Phase 8).

Currently used for GitHub OAuth access tokens: an integration credential
must never sit in the database in plaintext. The Fernet key is derived from
`AUTH_SECRET` — the same secret already required in every real environment
(ADR-003) — so no separate key needs provisioning or rotation.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet(auth_secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(auth_secret.encode()).digest())
    return Fernet(key)


def encrypt_secret(plaintext: str, *, auth_secret: str) -> str:
    return _fernet(auth_secret).encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str, *, auth_secret: str) -> str:
    try:
        return _fernet(auth_secret).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt stored secret.") from exc
