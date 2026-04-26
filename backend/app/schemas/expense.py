"""
PALA — Expense Schemas
Request/response schemas for expense CRUD endpoints.
FR-M15: Predefined expense categories.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    """Predefined expense categories per FR-M15."""
    FOOD_DINING = "Food & Dining"
    TRANSPORTATION = "Transportation"
    ENTERTAINMENT = "Entertainment"
    HEALTH = "Health"
    SHOPPING = "Shopping"
    UTILITIES = "Utilities"
    EDUCATION = "Education"
    OTHER = "Other"


class ExpenseCreate(BaseModel):
    """Expense creation payload."""
    amount: float = Field(..., gt=0, examples=[250.50])
    currency: str = Field(default="INR", min_length=3, max_length=3, examples=["INR"])
    category: str = Field(..., min_length=1, max_length=100, examples=["Food & Dining"])
    description: str | None = Field(default=None, max_length=500, examples=["Lunch at office canteen"])
    expense_at: datetime = Field(..., examples=["2026-04-25T12:30:00Z"])


class ExpenseUpdate(BaseModel):
    """Expense update payload — all fields optional."""
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    expense_at: datetime | None = None


class ExpenseResponse(BaseModel):
    """Expense record returned from API."""
    id: int
    user_id: str
    amount: float
    currency: str
    category: str
    description: str | None
    expense_at: datetime
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}
