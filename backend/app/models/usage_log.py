"""
PALA — Usage Log Model
SRS §6.2: Usage Logs table — tracks daily app usage duration per user.
"""

from datetime import datetime, date, timezone

from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UsageLog(Base):
    """Usage Logs table — daily app usage records."""

    __tablename__ = "usage_logs"
    __table_args__ = (
        # Prevent duplicate records for same user + app + date
        UniqueConstraint("user_id", "app_package", "recorded_date", name="uq_usage_user_app_date"),
    )

    # PK: Auto-incrementing integer
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # FK → Users.id — cascades on user delete
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # e.g. com.instagram.android
    app_package: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Human-readable app name
    app_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Daily total in seconds
    time_spent_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # UTC calendar date of usage
    recorded_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # When record arrived at server
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # ── Relationship ──────────────────────────────────────────
    user = relationship("User", back_populates="usage_logs")

    def __repr__(self) -> str:
        return f"<UsageLog(user={self.user_id}, app={self.app_label}, date={self.recorded_date})>"
