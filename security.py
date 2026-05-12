"""
Password hashing and credential loading helpers.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
from typing import Mapping, Optional


HASH_ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 600_000


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Return a salted PBKDF2 password hash suitable for Streamlit secrets."""
    if not password:
        raise ValueError("Password must not be empty")

    salt = secrets.token_urlsafe(24)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    digest_b64 = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{HASH_ALGORITHM}${iterations}${salt}${digest_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations_raw, salt, expected_b64 = password_hash.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False

        iterations = int(iterations_raw)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        actual_b64 = base64.urlsafe_b64encode(digest).decode("ascii")
        return hmac.compare_digest(actual_b64, expected_b64)
    except (TypeError, ValueError):
        return False


def _env_var_for_user(username: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", username).upper().strip("_")
    return f"PORTFOLIO_PASSWORD_HASH_{normalized}"


def get_configured_password_hash(username: str, secrets_mapping: Optional[Mapping] = None) -> Optional[str]:
    """
    Load a user's password hash from Streamlit secrets or environment variables.

    Preferred Streamlit format:

        [password_hashes]
        annika = "pbkdf2_sha256$..."

    Environment fallback:

        PORTFOLIO_PASSWORD_HASH_ANNIKA="pbkdf2_sha256$..."
    """
    user_key = username.strip().lower()

    if secrets_mapping is None:
        try:
            import streamlit as st

            secrets_mapping = st.secrets
        except Exception:
            secrets_mapping = {}

    try:
        password_hashes = secrets_mapping.get("password_hashes", {})
        configured_hash = password_hashes.get(user_key)
        if configured_hash:
            return str(configured_hash)
    except Exception:
        pass

    return os.environ.get(_env_var_for_user(user_key))
