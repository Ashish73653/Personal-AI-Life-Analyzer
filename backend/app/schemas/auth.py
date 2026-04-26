"""
PALA — Authentication Schemas
Registration/login request/response validation.
FR-M1: Password strength — min 8 chars, 1 uppercase, 1 digit.
"""

import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    """User registration payload."""
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        FR-M1: min 8 chars, at least 1 uppercase, at least 1 digit.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login payload."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned after login/register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token payload."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user data (never exposes password_hash)."""
    id: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
