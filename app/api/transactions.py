from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.accounts import get_account_or_404
from app.api.dependencies import require_roles
from app.core.constants import AccountStatus, TransactionStatus, TransactionType, UserRole
from app.core.security import generate_reference, utc_now
from app.db.session import get_db
from app.models import Account, Beneficiary, Transaction, User
from app.schemas import (
    BeneficiaryCreate,
    BeneficiaryRead,
    DepositRequest,
    ScheduledTransferRequest,
    TransactionRead,
    TransferRequest,
    WithdrawalRequest,
)


router = APIRouter(prefix="/transactions", tags=["Transactions"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def ensure_active(account: Account) -> None:
    if account.status != AccountStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not active")


def create_transaction(
    db: Session,
    transaction_type: str,
    channel: str,
    amount: Decimal,
    from_account_id: int | None = None,
    to_account_id: int | None = None,
    description: str | None = None,
    status_value: str = TransactionStatus.SUCCESS.value,
):
    transaction = Transaction(
        reference_no=generate_reference("TXN"),
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        transaction_type=transaction_type,
        channel=channel,
        amount=amount,
        status=status_value,
        description=description,
        created_at=utc_now(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.post("/deposit", response_model=TransactionRead)
def deposit(payload: DepositRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Transaction:
    account = get_account_or_404(db, payload.account_id)
    ensure_active(account)
    account.balance += payload.amount
    return create_transaction(
        db,
        TransactionType.DEPOSIT.value,
        "branch",
        payload.amount,
        to_account_id=account.id,
        description=payload.description,
    )


@router.post("/withdrawal", response_model=TransactionRead)
def withdraw(payload: WithdrawalRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Transaction:
    account = get_account_or_404(db, payload.account_id)
    ensure_active(account)
    if account.balance < payload.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")
    account.balance -= payload.amount
    return create_transaction(
        db,
        TransactionType.WITHDRAWAL.value,
        "branch",
        payload.amount,
        from_account_id=account.id,
        description=payload.description,
    )


@router.post("/transfer", response_model=TransactionRead)
def fund_transfer(payload: TransferRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Transaction:
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose two different accounts")

    source = get_account_or_404(db, payload.from_account_id)
    destination = get_account_or_404(db, payload.to_account_id)
    ensure_active(source)
    ensure_active(destination)

    if source.balance < payload.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    source.balance -= payload.amount
    destination.balance += payload.amount
    return create_transaction(
        db,
        payload.transaction_type.value,
        "online",
        payload.amount,
        source.id,
        destination.id,
        payload.description,
    )


@router.post("/upi", response_model=TransactionRead)
def upi_transfer(payload: TransferRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Transaction:
    payload.transaction_type = TransactionType.UPI
    return fund_transfer(payload, db, user)


@router.post("/neft", response_model=TransactionRead)
def neft_transfer(payload: TransferRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Transaction:
    payload.transaction_type = TransactionType.NEFT
    return fund_transfer(payload, db, user)


@router.post("/rtgs", response_model=TransactionRead)
def rtgs_transfer(payload: TransferRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Transaction:
    payload.transaction_type = TransactionType.RTGS
    return fund_transfer(payload, db, user)


@router.post("/scheduled", response_model=TransactionRead)
def schedule_transfer(payload: ScheduledTransferRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Transaction:
    source = get_account_or_404(db, payload.from_account_id)
    destination = get_account_or_404(db, payload.to_account_id)
    ensure_active(source)
    ensure_active(destination)

    transaction = Transaction(
        reference_no=generate_reference("SCH"),
        from_account_id=source.id,
        to_account_id=destination.id,
        transaction_type=payload.transaction_type.value,
        channel="scheduled",
        amount=payload.amount,
        status=TransactionStatus.SCHEDULED.value,
        description=payload.description,
        scheduled_for=payload.scheduled_for,
        created_at=utc_now(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/history", response_model=list[TransactionRead])
def history(
    account_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> list[Transaction]:
    query = select(Transaction).order_by(Transaction.id.desc())
    if account_id:
        query = query.where((Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id))
    return list(db.scalars(query).all())


@router.post("/beneficiaries", response_model=BeneficiaryRead, status_code=status.HTTP_201_CREATED)
def add_beneficiary(payload: BeneficiaryCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Beneficiary:
    beneficiary = Beneficiary(**payload.model_dump())
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


@router.get("/beneficiaries", response_model=list[BeneficiaryRead])
def list_beneficiaries(customer_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> list[Beneficiary]:
    return list(db.scalars(select(Beneficiary).where(Beneficiary.customer_id == customer_id)).all())
