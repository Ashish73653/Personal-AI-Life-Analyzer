"""
PALA — Step Model
SRS §6.2: Steps table — daily step count records with unique (user_id, step_date).
"""

from datetime import datetime, date, timezone

from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Step(Base):
    """Steps table — daily step count records."""

    __tablename__ = "steps"
    __table_args__ = (
        # One step record per user per day (SRS FR-B8)
        UniqueConstraint("user_id", "step_date", name="uq_steps_user_date"),
    )

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

    # Daily total steps
    step_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # UTC date
    step_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Data source: "sensor" or "google_fit"
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="sensor",
    )

    # When record arrived at server
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # ── Relationship ──────────────────────────────────────────
    user = relationship("User", back_populates="steps")

    def __repr__(self) -> str:
        return f"<Step(user={self.user_id}, date={self.step_date}, count={self.step_count})>"
