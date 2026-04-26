"""
PALA — Rate Limiter
SEC-5: Max 60 requests/minute per user to prevent brute-force attacks.
Uses SlowAPI with in-memory storage for development.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.services.auth_service import decode_token

settings = get_settings()


def _rate_limit_key(request: Request) -> str:
    """Prefer authenticated user id; fall back to client IP."""
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if payload and payload.get("type") == "access" and payload.get("sub"):
            return f"user:{payload['sub']}"

    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


# Rate limiter — keyed by authenticated user when available.
limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)

slowapi_middleware = SlowAPIMiddleware
