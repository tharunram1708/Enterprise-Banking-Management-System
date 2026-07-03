from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import TransactionStatus, UserRole
from app.db.session import get_db
from app.models import Account, Customer, Loan, Transaction, User


router = APIRouter(prefix="/reports", tags=["Reports & Dashboard"])
admin_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value)


@router.get("/customer-dashboard/{customer_id}")
def customer_dashboard(customer_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    account_count = db.scalar(select(func.count(Account.id)).where(Account.customer_id == customer_id)) or 0
    loan_count = db.scalar(select(func.count(Loan.id)).where(Loan.customer_id == customer_id)) or 0
    balance = db.scalar(select(func.coalesce(func.sum(Account.balance), 0)).where(Account.customer_id == customer_id)) or 0
    return {"customer_id": customer_id, "accounts": account_count, "loans": loan_count, "total_balance": balance}


@router.get("/admin-dashboard")
def admin_dashboard(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    return {
        "customers": db.scalar(select(func.count(Customer.id))) or 0,
        "accounts": db.scalar(select(func.count(Account.id))) or 0,
        "loans": db.scalar(select(func.count(Loan.id))) or 0,
        "transactions": db.scalar(select(func.count(Transaction.id))) or 0,
    }


@router.get("/revenue")
def revenue_report(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    deposits = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_type == "deposit",
            Transaction.status == TransactionStatus.SUCCESS.value,
        )
    ) or 0
    return {"deposit_volume": deposits, "service_fee_revenue_mock": 0}


@router.get("/transactions")
def transaction_report(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    total = db.scalar(select(func.count(Transaction.id))) or 0
    failed = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "failed")) or 0
    return {"total_transactions": total, "failed_transactions": failed}


@router.get("/loans")
def loan_report(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    active = db.scalar(select(func.count(Loan.id)).where(Loan.status == "active")) or 0
    closed = db.scalar(select(func.count(Loan.id)).where(Loan.status == "closed")) or 0
    return {"active_loans": active, "closed_loans": closed}


@router.get("/fraud")
def fraud_report(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    high_value_count = db.scalar(select(func.count(Transaction.id)).where(Transaction.amount >= 1000000)) or 0
    return {"high_value_transactions": high_value_count, "review_required": high_value_count > 0}
