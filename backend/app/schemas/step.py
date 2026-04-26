"""
PALA — Step Schemas
Request/response schemas for step tracking endpoints.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field


class StepCreate(BaseModel):
    """Step record submission (upserts on user_id + step_date)."""
    step_count: int = Field(..., ge=0, examples=[8500])
    step_date: date = Field(..., examples=["2026-04-25"])
    source: str = Field(default="sensor", pattern=r"^(sensor|google_fit)$", examples=["sensor"])


class StepResponse(BaseModel):
    """Step record returned from API."""
    id: int
    user_id: str
    step_count: int
    step_date: date
    source: str
    synced_at: datetime

    model_config = {"from_attributes": True}
