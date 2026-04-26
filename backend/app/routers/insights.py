"""
PALA — Insights Router
FR-B18: Daily summary narrative.
FR-B19: Weekly report with trend comparisons.
FR-B20: ≥3 prioritized recommendations per weekly report.
FR-B21: GET /insights?type=daily|weekly&date=
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.common import success_response
from app.services.analytics_service import build_daily_summary, build_weekly_report

router = APIRouter(prefix="/insights", tags=["AI Insights"])


@router.get("")
def get_insights(
    type: str = Query(default="daily", pattern=r"^(daily|weekly)$", description="daily or weekly"),
    day: date | None = Query(default=None, alias="date", description="Target date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FR-B21: Retrieve AI-generated insights.
    - type=daily  → single day summary (defaults to yesterday)
    - type=weekly → 7-day report starting from most recent Monday
    """
    target_date = day or (date.today() - timedelta(days=1))

    if type == "daily":
        summary = build_daily_summary(db, current_user.id, target_date)
        return success_response(data=summary)

    else:  # weekly
        # Snap to the Monday of the target week
        week_start = target_date - timedelta(days=target_date.weekday())
        report = build_weekly_report(db, current_user.id, week_start)
        return success_response(data=report)


@router.get("/today")
def get_today_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convenience endpoint — returns today's partial summary."""
    summary = build_daily_summary(db, current_user.id, date.today())
    return success_response(data=summary)
