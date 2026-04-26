"""
PALA — Authentication Service
Handles password hashing (bcrypt ≥ 12 rounds) and JWT token lifecycle.
SEC-2: Access 15 min, refresh 7 days, rotation on use.
SEC-3: bcrypt cost factor ≥ 12.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.config import get_settings

settings = get_settings()


# ── Password Hashing ─────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt with configurable rounds."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT Token Management ─────────────────────────────────────
def create_access_token(user_id: str) -> str:
    """
    Create a short-lived access token.
    SEC-2: Default expiry = 15 minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_token_payload(user_id=user_id, token_type="access", expires_at=expire, token_version=0)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh token.
    SEC-2: Default expiry = 7 days, rotated on each use.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_token_payload(user_id=user_id, token_type="refresh", expires_at=expire, token_version=0)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token_with_version(user_id: str, token_version: int) -> str:
    """Create an access token bound to the current user token version."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_token_payload(user_id=user_id, token_type="access", expires_at=expire, token_version=token_version)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token_with_version(user_id: str, token_version: int) -> str:
    """Create a refresh token bound to the current user token version."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_token_payload(user_id=user_id, token_type="refresh", expires_at=expire, token_version=token_version)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decode and validate a JWT token.
    Returns the payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def _build_token_payload(user_id: str, token_type: str, expires_at: datetime, token_version: int) -> dict:
    return {
        "sub": user_id,
        "exp": expires_at,
        "type": token_type,
        "ver": token_version,
    }
