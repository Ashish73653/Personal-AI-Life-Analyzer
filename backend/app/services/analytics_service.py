"""
PALA — Pattern Detection Service
FR-B16: Detects high screen time events (daily total > threshold, default 6h).
FR-B17: Detects low physical activity days (steps < threshold, default 5000).
FR-B18: Generates daily summary narratives.
FR-B19/20: Weekly reports with recommendations.
"""

from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.usage_log import UsageLog
from app.models.step import Step
from app.models.expense import Expense


# ── Configurable Thresholds ───────────────────────────────────
HIGH_SCREEN_TIME_HOURS = 6          # FR-B16 default
LOW_STEP_COUNT = 5_000              # FR-B17 default
SECONDS_PER_HOUR = 3600


# ── Screen Time Analysis ──────────────────────────────────────
def get_daily_screen_time_seconds(db: Session, user_id: str, day: date) -> int:
    """Sum total screen time in seconds for a user on a given date."""
    rows = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.recorded_date == day,
    ).all()
    return sum(r.time_spent_sec for r in rows)


def get_top_apps(db: Session, user_id: str, day: date, top_n: int = 5) -> list[dict]:
    """Return top-N apps by time spent for a user on a given date."""
    rows = (
        db.query(UsageLog)
        .filter(UsageLog.user_id == user_id, UsageLog.recorded_date == day)
        .order_by(UsageLog.time_spent_sec.desc())
        .limit(top_n)
        .all()
    )
    return [
        {
            "app_label": r.app_label,
            "app_package": r.app_package,
            "time_spent_sec": r.time_spent_sec,
            "time_spent_hours": round(r.time_spent_sec / SECONDS_PER_HOUR, 2),
        }
        for r in rows
    ]


def is_high_screen_time(total_seconds: int, threshold_hours: float = HIGH_SCREEN_TIME_HOURS) -> bool:
    """FR-B16: True if total daily screen time exceeds threshold."""
    return total_seconds > (threshold_hours * SECONDS_PER_HOUR)


# ── Step Analysis ─────────────────────────────────────────────
def get_daily_steps(db: Session, user_id: str, day: date) -> int | None:
    """Return step count for a user on a given date, or None if no record."""
    row = db.query(Step).filter(
        Step.user_id == user_id,
        Step.step_date == day,
    ).first()
    return row.step_count if row else None


def is_low_activity(step_count: int | None, threshold: int = LOW_STEP_COUNT) -> bool:
    """FR-B17: True if step count is below threshold (or missing)."""
    if step_count is None:
        return True
    return step_count < threshold


# ── Expense Analysis ──────────────────────────────────────────
def get_daily_expenses(db: Session, user_id: str, day: date) -> list[dict]:
    """Return expenses for a user on a given date."""
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    rows = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.expense_at >= start,
        Expense.expense_at < end,
        Expense.is_deleted == False,  # noqa: E712
    ).all()
    return [
        {
            "amount": float(r.amount),
            "currency": r.currency,
            "category": r.category,
            "description": r.description,
        }
        for r in rows
    ]


def get_expense_summary_by_category(db: Session, user_id: str, start: date, end: date) -> dict:
    """Return total spend per category over a date range."""
    start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    rows = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.expense_at >= start_dt,
        Expense.expense_at < end_dt,
        Expense.is_deleted == False,  # noqa: E712
    ).all()
    totals: dict[str, float] = {}
    for r in rows:
        totals[r.category] = totals.get(r.category, 0.0) + float(r.amount)
    return totals


# ── Daily Summary Builder ─────────────────────────────────────
def build_daily_summary(db: Session, user_id: str, day: date) -> dict:
    """
    FR-B18: Build a structured daily summary for a given date.
    Returns a dict ready to store or return via API.
    """
    total_screen_sec = get_daily_screen_time_seconds(db, user_id, day)
    top_apps = get_top_apps(db, user_id, day)
    steps = get_daily_steps(db, user_id, day)
    expenses = get_daily_expenses(db, user_id, day)
    total_expense = sum(e["amount"] for e in expenses)

    high_screen = is_high_screen_time(total_screen_sec)
    low_activity = is_low_activity(steps)

    # Build natural-language narrative
    screen_hours = total_screen_sec / SECONDS_PER_HOUR
    top_app_str = f" (top app: {top_apps[0]['app_label']})" if top_apps else ""
    narrative_parts = [
        f"On {day}, you spent {screen_hours:.1f}h on your phone{top_app_str}.",
    ]
    if steps is not None:
        narrative_parts.append(f"You walked {steps:,} steps.")
    else:
        narrative_parts.append("No step data recorded.")

    if expenses:
        narrative_parts.append(f"You spent {total_expense:.2f} across {len(expenses)} expense(s).")
    else:
        narrative_parts.append("No expenses logged.")

    flags = []
    if high_screen:
        flags.append(f"HIGH_SCREEN_TIME (>{HIGH_SCREEN_TIME_HOURS}h)")
    if low_activity:
        flags.append(f"LOW_ACTIVITY (<{LOW_STEP_COUNT:,} steps)")

    return {
        "date": str(day),
        "type": "daily",
        "screen_time_seconds": total_screen_sec,
        "screen_time_hours": round(screen_hours, 2),
        "top_apps": top_apps,
        "step_count": steps,
        "total_expense": round(total_expense, 2),
        "expense_breakdown": get_expense_summary_by_category(db, user_id, day, day),
        "flags": flags,
        "narrative": " ".join(narrative_parts),
    }


# ── Weekly Report Builder ─────────────────────────────────────
def build_weekly_report(db: Session, user_id: str, week_start: date) -> dict:
    """
    FR-B19/20: Build a weekly report covering 7 days starting from week_start.
    Includes trend data and at least 3 recommendations.
    """
    week_end = week_start + timedelta(days=6)
    daily_summaries = []

    total_screen_sec = 0
    total_steps = 0
    step_days = 0
    high_screen_days = 0
    low_activity_days = 0

    for i in range(7):
        day = week_start + timedelta(days=i)
        summary = build_daily_summary(db, user_id, day)
        daily_summaries.append(summary)
        total_screen_sec += summary["screen_time_seconds"]
        if summary["step_count"] is not None:
            total_steps += summary["step_count"]
            step_days += 1
        if "HIGH_SCREEN_TIME" in " ".join(summary["flags"]):
            high_screen_days += 1
        if "LOW_ACTIVITY" in " ".join(summary["flags"]):
            low_activity_days += 1

    avg_screen_hours = (total_screen_sec / SECONDS_PER_HOUR) / 7
    avg_steps = total_steps / step_days if step_days > 0 else 0
    total_expense = sum(d["total_expense"] for d in daily_summaries)
    expense_by_cat = get_expense_summary_by_category(db, user_id, week_start, week_end)

    # FR-B20: Generate ≥3 prioritized recommendations
    recommendations = _generate_recommendations(
        avg_screen_hours=avg_screen_hours,
        avg_steps=avg_steps,
        high_screen_days=high_screen_days,
        low_activity_days=low_activity_days,
        expense_by_cat=expense_by_cat,
        total_expense=total_expense,
    )

    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "type": "weekly",
        "avg_screen_time_hours": round(avg_screen_hours, 2),
        "total_screen_time_hours": round(total_screen_sec / SECONDS_PER_HOUR, 2),
        "avg_steps": round(avg_steps),
        "total_steps": total_steps,
        "high_screen_days": high_screen_days,
        "low_activity_days": low_activity_days,
        "total_expense": round(total_expense, 2),
        "expense_by_category": expense_by_cat,
        "daily_summaries": daily_summaries,
        "recommendations": recommendations,
    }


def _generate_recommendations(
    avg_screen_hours: float,
    avg_steps: float,
    high_screen_days: int,
    low_activity_days: int,
    expense_by_cat: dict,
    total_expense: float,
) -> list[dict]:
    """
    FR-B20: Generate ≥3 prioritized recommendations based on detected patterns.
    """
    recs = []

    # Screen time recommendations
    if high_screen_days >= 5:
        recs.append({
            "priority": 1,
            "category": "screen_time",
            "title": "Reduce daily screen time",
            "message": (
                f"You exceeded {HIGH_SCREEN_TIME_HOURS}h of screen time on {high_screen_days}/7 days. "
                "Try enabling app timers for your top apps to cap usage at 2h/day."
            ),
        })
    elif avg_screen_hours > 4:
        recs.append({
            "priority": 2,
            "category": "screen_time",
            "title": "Monitor screen time trends",
            "message": (
                f"Your average screen time was {avg_screen_hours:.1f}h/day this week. "
                "Consider a no-phone hour before bed to improve sleep quality."
            ),
        })

    # Activity recommendations
    if low_activity_days >= 5:
        recs.append({
            "priority": 1,
            "category": "activity",
            "title": "Increase daily movement",
            "message": (
                f"You had low activity ({LOW_STEP_COUNT:,} steps) on {low_activity_days}/7 days. "
                "Try adding a 20-minute walk to your daily routine."
            ),
        })
    elif low_activity_days >= 2:
        recs.append({
            "priority": 2,
            "category": "activity",
            "title": "Weekend activity dip detected",
            "message": (
                f"Your step count dropped on {low_activity_days} days this week. "
                "Consider a weekend walk or outdoor activity to maintain consistency."
            ),
        })

    # Expense recommendations
    if total_expense > 0:
        top_category = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else None
        if top_category:
            top_amount = expense_by_cat[top_category]
            top_pct = (top_amount / total_expense) * 100
            if top_pct > 50:
                recs.append({
                    "priority": 2,
                    "category": "expenses",
                    "title": f"High spending in {top_category}",
                    "message": (
                        f"{top_category} accounted for {top_pct:.0f}% of your weekly spend "
                        f"(₹{top_amount:.2f}). Consider setting a budget limit for this category."
                    ),
                })

    # Always ensure at least 3 recommendations
    defaults = [
        {
            "priority": 3,
            "category": "wellness",
            "title": "Track your expenses daily",
            "message": "Logging expenses right after spending helps build financial awareness.",
        },
        {
            "priority": 3,
            "category": "activity",
            "title": "Aim for 8,000 steps/day",
            "message": "Research shows 8,000 steps/day is associated with reduced health risks.",
        },
        {
            "priority": 3,
            "category": "screen_time",
            "title": "Use grayscale mode at night",
            "message": "Grayscale display reduces the visual appeal of apps and can cut usage by 20%.",
        },
    ]
    for d in defaults:
        if len(recs) >= 3:
            break
        recs.append(d)

    return sorted(recs, key=lambda r: r["priority"])
