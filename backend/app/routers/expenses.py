"""
PALA — Expenses Router
FR-B4: Full CRUD for expenses.
POST   /expenses       — create expense
GET    /expenses       — list expenses (excludes soft-deleted)
PUT    /expenses/{id}  — update expense
DELETE /expenses/{id}  — soft-delete expense
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.schemas.common import success_response

router = APIRouter(prefix="/expenses", tags=["Expense Tracking"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new expense entry.
    FR-M12: Amount, currency (ISO 4217), category, optional description, timestamp.
    """
    expense = Expense(
        user_id=current_user.id,
        amount=body.amount,
        currency=body.currency.upper(),
        category=body.category,
        description=body.description,
        expense_at=body.expense_at,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return success_response(
        data=ExpenseResponse.model_validate(expense).model_dump()
    )


@router.get("")
def get_expenses(
    category: str | None = Query(default=None, description="Filter by category"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Skip N records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List expenses (excludes soft-deleted).
    FR-B4: GET /expenses with filtering and pagination.
    SEC-8: User data isolation enforced at query level.
    """
    query = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.is_deleted == False,  # noqa: E712
    )

    if category:
        query = query.filter(Expense.category == category)

    total = query.count()
    expenses = query.order_by(Expense.expense_at.desc()).offset(offset).limit(limit).all()

    return success_response(data={
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [ExpenseResponse.model_validate(e).model_dump() for e in expenses],
    })


@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    body: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing expense.
    FR-M13: All field changes recorded with updated_at timestamp.
    SEC-8: Enforces user ownership at query level.
    """
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
        Expense.is_deleted == False,  # noqa: E712
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    # Apply partial update — only set fields that were provided
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "currency" and value:
            value = value.upper()
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    return success_response(
        data=ExpenseResponse.model_validate(expense).model_dump()
    )


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete an expense.
    FR-M14: Retained in DB with is_deleted flag for 30 days before permanent removal.
    """
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
        Expense.is_deleted == False,  # noqa: E712
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    expense.is_deleted = True
    db.commit()

    return success_response(data={"message": "Expense deleted successfully"})
