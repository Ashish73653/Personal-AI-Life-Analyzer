"""
PALA — Steps Router
FR-B3: CRUD endpoints for step records.
POST /steps — submit step record (upsert on user_id + step_date).
GET  /steps — query by date range.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.step import Step
from app.schemas.step import StepCreate, StepResponse
from app.schemas.common import success_response

router = APIRouter(prefix="/steps", tags=["Step Tracking"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_or_update_steps(
    body: StepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a step record.
    Upserts on (user_id, step_date) — if a record already exists for
    that date, it updates the step_count and source.
    FR-M18: Idempotent upsert to prevent duplication.
    """
    existing = db.query(Step).filter(
        Step.user_id == current_user.id,
        Step.step_date == body.step_date,
    ).first()

    if existing:
        existing.step_count = body.step_count
        existing.source = body.source
        step = existing
    else:
        step = Step(
            user_id=current_user.id,
            step_count=body.step_count,
            step_date=body.step_date,
            source=body.source,
        )
        db.add(step)

    db.commit()
    db.refresh(step)

    return success_response(
        data=StepResponse.model_validate(step).model_dump()
    )


@router.get("")
def get_steps(
    start: date | None = Query(default=None, description="Start of date range"),
    end: date | None = Query(default=None, description="End of date range"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Query step records with optional date range filtering.
    FR-B3: GET /steps?start=&end=
    """
    query = db.query(Step).filter(Step.user_id == current_user.id)

    if start:
        query = query.filter(Step.step_date >= start)
    if end:
        query = query.filter(Step.step_date <= end)

    steps = query.order_by(Step.step_date.desc()).all()

    return success_response(
        data=[StepResponse.model_validate(s).model_dump() for s in steps]
    )
