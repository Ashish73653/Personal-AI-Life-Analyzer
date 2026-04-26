"""
PALA — Usage Router
FR-B2: CRUD endpoints for usage logs.
POST /usage — submit usage log(s) with batch upsert.
GET  /usage — query by date or date range.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.usage_log import UsageLog
from app.schemas.usage_log import UsageLogCreate, UsageLogBatchCreate, UsageLogResponse
from app.schemas.common import success_response

router = APIRouter(prefix="/usage", tags=["Usage Tracking"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_usage_logs(
    body: UsageLogBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit one or more usage log entries.
    FR-M18: Uses upsert strategy to prevent duplication during partial sync failures.
    """
    created = []

    for log_data in body.logs:
        # Check for existing record (idempotent upsert)
        existing = db.query(UsageLog).filter(
            UsageLog.user_id == current_user.id,
            UsageLog.app_package == log_data.app_package,
            UsageLog.recorded_date == log_data.recorded_date,
        ).first()

        if existing:
            # Update existing record
            existing.app_label = log_data.app_label
            existing.time_spent_sec = log_data.time_spent_sec
            created.append(existing)
        else:
            # Create new record
            usage_log = UsageLog(
                user_id=current_user.id,
                app_package=log_data.app_package,
                app_label=log_data.app_label,
                time_spent_sec=log_data.time_spent_sec,
                recorded_date=log_data.recorded_date,
            )
            db.add(usage_log)
            created.append(usage_log)

    db.commit()

    # Refresh all to get generated IDs and synced_at
    for item in created:
        db.refresh(item)

    return success_response(
        data=[UsageLogResponse.model_validate(u).model_dump() for u in created]
    )


@router.get("")
def get_usage_logs(
    recorded_date: date | None = Query(default=None, description="Filter by exact date"),
    start: date | None = Query(default=None, description="Start of date range"),
    end: date | None = Query(default=None, description="End of date range"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Query usage logs with optional date filtering.
    FR-B2: GET /usage?date=&user_id= (user_id from JWT).
    """
    query = db.query(UsageLog).filter(UsageLog.user_id == current_user.id)

    if recorded_date:
        query = query.filter(UsageLog.recorded_date == recorded_date)
    elif start and end:
        query = query.filter(UsageLog.recorded_date >= start, UsageLog.recorded_date <= end)
    elif start:
        query = query.filter(UsageLog.recorded_date >= start)
    elif end:
        query = query.filter(UsageLog.recorded_date <= end)

    logs = query.order_by(UsageLog.recorded_date.desc(), UsageLog.time_spent_sec.desc()).all()

    return success_response(
        data=[UsageLogResponse.model_validate(u).model_dump() for u in logs]
    )
