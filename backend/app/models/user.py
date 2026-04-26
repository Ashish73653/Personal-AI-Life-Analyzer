"""
PALA — User Model
SRS §6.2: Users table with UUID PK, unique email, bcrypt hash, soft-disable.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Users table — stores account credentials and metadata."""

    __tablename__ = "users"

    # PK: Auto-generated UUID v4
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # Unique email — lowercased and trimmed on insert
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # bcrypt hash, cost factor ≥ 12
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Account creation time (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # Auto-updated on any change
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # Soft-disable without deletion
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ── Relationships ─────────────────────────────────────────
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    steps = relationship("Step", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
