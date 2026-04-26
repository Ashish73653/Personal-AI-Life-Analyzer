"""
PALA — Query Router (RAG / NL Interface)
FR-B22: POST /query — accepts NL question, returns AI-generated answer.
FR-B23: Processes through RAG pipeline (Phase 3 — Ollama wired in).
FR-B24: GET /query/history — per-user query history.

Phase 1: Returns a structured stub response so the Android app
         and web dashboard can be built against this contract now.
         The actual Ollama/FAISS pipeline is wired in Phase 3.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.database import Base
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.query_history import QueryHistory
from app.schemas.common import success_response

router = APIRouter(prefix="/query", tags=["AI Query"])


# ── Schemas ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    """FR-B22: NL query payload."""
    question: str = Field(..., min_length=3, max_length=1000, examples=["Where do I waste the most time?"])


class QueryResponse(BaseModel):
    """AI-generated answer with context metadata."""
    question: str
    answer: str
    sources_used: int
    model_used: str
    asked_at: datetime


# ── Endpoints ─────────────────────────────────────────────────
@router.post("")
def query_ai(
    body: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FR-B22/23: Submit a natural-language question about your data.

    Phase 1: Returns a helpful stub response with data context.
    Phase 3: This will route through the full RAG pipeline
             (FAISS retrieval → Ollama LLM inference).
    """
    from app.services.analytics_service import build_daily_summary
    from datetime import date, timedelta

    # Build some context from recent data to show in stub
    yesterday = date.today() - timedelta(days=1)
    context = build_daily_summary(db, current_user.id, yesterday)

    # Phase 1 stub — will be replaced with real RAG in Phase 3
    stub_answer = (
        f"[AI Engine — Phase 3 Pending] I can see your data: "
        f"Yesterday you had {context['screen_time_hours']}h screen time, "
        f"{context['step_count'] or 'unknown'} steps, and spent "
        f"₹{context['total_expense']} on expenses. "
        f"Once the Ollama RAG pipeline is wired up in Phase 3, "
        f"I'll give you a real answer to: '{body.question}'"
    )

    # Store in query history (FR-B24)
    record = QueryHistory(
        user_id=current_user.id,
        question=body.question,
        answer=stub_answer,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(data=QueryResponse(
        question=body.question,
        answer=stub_answer,
        sources_used=0,
        model_used="stub-phase1",
        asked_at=record.asked_at,
    ).model_dump())


@router.get("/history")
def get_query_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FR-B24: Retrieve the authenticated user's query history.
    """
    records = (
        db.query(QueryHistory)
        .filter(QueryHistory.user_id == current_user.id)
        .order_by(QueryHistory.asked_at.desc())
        .limit(limit)
        .all()
    )
    return success_response(data=[
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "asked_at": r.asked_at.isoformat(),
        }
        for r in records
    ])
