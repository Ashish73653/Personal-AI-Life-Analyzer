"""
PALA — Auth Router
FR-B1: POST /auth/register and POST /auth/login (public endpoints).
SEC-2: JWT access + refresh tokens with rotation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.schemas.common import success_response, error_response
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token_with_version,
    create_refresh_token_with_version,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user account.
    FR-B1: Returns JWT access and refresh tokens upon successful registration.
    """
    # Normalize email
    email = body.email.lower().strip()

    # Check for existing user
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user
    user = User(
        email=email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue tokens
    tokens = TokenResponse(
        access_token=create_access_token_with_version(user.id, user.token_version),
        refresh_token=create_refresh_token_with_version(user.id, user.token_version),
    )

    return success_response(data={
        "user": UserResponse.model_validate(user).model_dump(),
        "tokens": tokens.model_dump(),
    })


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.
    FR-B1: Returns JWT access and refresh tokens on success.
    """
    email = body.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    tokens = TokenResponse(
        access_token=create_access_token_with_version(user.id, user.token_version),
        refresh_token=create_refresh_token_with_version(user.id, user.token_version),
    )

    return success_response(data={
        "user": UserResponse.model_validate(user).model_dump(),
        "tokens": tokens.model_dump(),
    })


@router.post("/refresh")
def refresh_tokens(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Rotate refresh token and issue a new access + refresh pair.
    SEC-2: Refresh tokens are rotated on each use.
    """
    payload = decode_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — refresh token required",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if payload.get("ver", 0) != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user.token_version += 1
    db.commit()
    db.refresh(user)

    # Issue new token pair (rotation)
    tokens = TokenResponse(
        access_token=create_access_token_with_version(user.id, user.token_version),
        refresh_token=create_refresh_token_with_version(user.id, user.token_version),
    )

    return success_response(data={"tokens": tokens.model_dump()})


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Mobile app uses this to validate a stored token is still valid.
    """
    return success_response(data=UserResponse.model_validate(current_user).model_dump())


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    FR-M3: Log out — client must discard tokens.
    JWT revocation is implemented by bumping the user's token version.
    """
    current_user.token_version += 1
    db.commit()
    return success_response(data={"message": "Logged out. Please clear your local tokens."})
