"""
PALA — Expense Model
SRS §6.2: Expenses table — user expense entries with soft delete support.
"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Expense(Base):
    """Expenses table — manual expense records with soft-delete."""

    __tablename__ = "expenses"

    # PK: Auto-incrementing integer
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # FK → Users.id
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Up to 10 digits + 2 decimal places
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # ISO 4217 currency code
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    # From predefined list or custom
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Optional user note
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # User-specified time of expense
    expense_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Record creation time
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

    # Soft delete — purged after 30 days
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── Relationship ──────────────────────────────────────────
    user = relationship("User", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense(user={self.user_id}, amount={self.amount}, category={self.category})>"
