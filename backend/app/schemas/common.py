"""
PALA — Common Schemas
Standard API response envelope per FR-B5.
"""

from typing import Any
from pydantic import BaseModel


class APIResponse(BaseModel):
    """
    Standard API response envelope.
    FR-B5: {"success": bool, "data": object | array, "error": string | null}
    """
    success: bool
    data: Any = None
    error: str | None = None


def success_response(data: Any = None) -> dict:
    """Helper to build a success envelope."""
    return {"success": True, "data": data, "error": None}


def error_response(error: str, data: Any = None) -> dict:
    """Helper to build an error envelope."""
    return {"success": False, "data": data, "error": error}
