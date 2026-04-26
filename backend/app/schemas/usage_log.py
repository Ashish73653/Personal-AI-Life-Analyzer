"""
PALA — Usage Log Schemas
Request/response schemas for app usage tracking endpoints.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field


class UsageLogCreate(BaseModel):
    """Single usage log entry for submission."""
    app_package: str = Field(..., min_length=1, max_length=255, examples=["com.instagram.android"])
    app_label: str = Field(..., min_length=1, max_length=255, examples=["Instagram"])
    time_spent_sec: int = Field(..., ge=0, examples=[3600])
    recorded_date: date = Field(..., examples=["2026-04-25"])


class UsageLogBatchCreate(BaseModel):
    """Batch submission of usage logs (supports sync from mobile)."""
    logs: list[UsageLogCreate]


class UsageLogResponse(BaseModel):
    """Usage log record returned from API."""
    id: int
    user_id: str
    app_package: str
    app_label: str
    time_spent_sec: int
    recorded_date: date
    synced_at: datetime

    model_config = {"from_attributes": True}
