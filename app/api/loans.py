from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import LoanStatus, UserRole
from app.core.security import utc_now
from app.db.session import get_db
from app.models import Customer, Loan, LoanRepaymentSchedule, User
from app.schemas import LoanCreate, LoanDecision, LoanRead, Message


router = APIRouter(prefix="/loans", tags=["Loan Management"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def calculate_emi(amount: Decimal, annual_rate: Decimal, months: int) -> Decimal:
    monthly_rate = annual_rate / Decimal("1200")
    if monthly_rate == 0:
        return (amount / months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    factor = (Decimal("1") + monthly_rate) ** months
    emi = amount * monthly_rate * factor / (factor - Decimal("1"))
    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_loan_or_404(db: Session, loan_id: int) -> Loan:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def apply_for_loan(payload: LoanCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Loan:
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    loan = Loan(
        customer_id=payload.customer_id,
        loan_type=payload.loan_type.value,
        amount=payload.amount,
        annual_interest_rate=payload.annual_interest_rate,
        tenure_months=payload.tenure_months,
        emi_amount=calculate_emi(payload.amount, payload.annual_interest_rate, payload.tenure_months),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@router.patch("/{loan_id}/decision", response_model=LoanRead)
def approve_or_reject_loan(
    loan_id: int,
    payload: LoanDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.MANAGER.value)),
) -> Loan:
    loan = get_loan_or_404(db, loan_id)
    loan.status = payload.status.value
    if payload.status == LoanStatus.APPROVED:
        loan.approved_by_user_id = current_user.id
    db.commit()
    db.refresh(loan)
    return loan


@router.get("", response_model=list[LoanRead])
def list_loans(db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> list[Loan]:
    return list(db.scalars(select(Loan).order_by(Loan.id.desc())).all())


@router.post("/{loan_id}/repayment-schedule", response_model=Message)
def create_repayment_schedule(loan_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Message:
    loan = get_loan_or_404(db, loan_id)
    existing = db.scalar(select(LoanRepaymentSchedule).where(LoanRepaymentSchedule.loan_id == loan.id))
    if existing:
        return Message(message="Repayment schedule already exists")

    principal_each_month = (loan.amount / loan.tenure_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    interest_each_month = (loan.emi_amount - principal_each_month).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    today = date.today()
    for installment_no in range(1, loan.tenure_months + 1):
        month = today.month + installment_no
        year = today.year + (month - 1) // 12
        due_month = ((month - 1) % 12) + 1
        db.add(
            LoanRepaymentSchedule(
                loan_id=loan.id,
                installment_no=installment_no,
                due_date=date(year, due_month, min(today.day, 28)),
                principal_amount=principal_each_month,
                interest_amount=interest_each_month,
                total_amount=loan.emi_amount,
            )
        )
    db.commit()
    return Message(message="Repayment schedule created")


@router.post("/{loan_id}/close", response_model=LoanRead)
def close_loan(loan_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.MANAGER.value))) -> Loan:
    loan = get_loan_or_404(db, loan_id)
    loan.status = LoanStatus.CLOSED.value
    loan.closed_at = utc_now()
    db.commit()
    db.refresh(loan)
    return loan
