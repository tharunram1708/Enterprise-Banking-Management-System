import secrets
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import AccountStatus, AccountType, UserRole
from app.db.session import get_db
from app.models import Account, Customer, User
from app.schemas import AccountCreate, AccountRead, AccountStatusUpdate


router = APIRouter(prefix="/accounts", tags=["Account Management"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def get_account_or_404(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


def make_account_number() -> str:
    return "10" + "".join(str(secrets.randbelow(10)) for _ in range(12))


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> Account:
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if payload.joint_holder_customer_id and not db.get(Customer, payload.joint_holder_customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Joint holder not found")

    account = Account(
        customer_id=payload.customer_id,
        account_number=make_account_number(),
        account_type=payload.account_type.value,
        balance=payload.opening_balance,
        interest_rate=payload.interest_rate,
        maturity_date=payload.maturity_date,
        joint_holder_customer_id=payload.joint_holder_customer_id,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/savings", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def open_savings_account(payload: AccountCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Account:
    payload.account_type = AccountType.SAVINGS
    return create_account(payload, db, user)


@router.post("/current", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def open_current_account(payload: AccountCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Account:
    payload.account_type = AccountType.CURRENT
    return create_account(payload, db, user)


@router.post("/fixed-deposits", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def open_fixed_deposit(payload: AccountCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Account:
    payload.account_type = AccountType.FIXED_DEPOSIT
    if not payload.maturity_date:
        payload.maturity_date = date.today().replace(year=date.today().year + 1)
    if payload.interest_rate is None:
        payload.interest_rate = Decimal("6.50")
    return create_account(payload, db, user)


@router.post("/recurring-deposits", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def open_recurring_deposit(payload: AccountCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*staff_roles))) -> Account:
    payload.account_type = AccountType.RECURRING_DEPOSIT
    if payload.interest_rate is None:
        payload.interest_rate = Decimal("6.25")
    return create_account(payload, db, user)


@router.get("", response_model=list[AccountRead])
def list_accounts(
    customer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> list[Account]:
    query = select(Account).order_by(Account.id.desc())
    if customer_id:
        query = query.where(Account.customer_id == customer_id)
    return list(db.scalars(query).all())


@router.patch("/{account_id}/status", response_model=AccountRead)
def update_account_status(
    account_id: int,
    payload: AccountStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.MANAGER.value)),
) -> Account:
    account = get_account_or_404(db, account_id)
    account.status = payload.status.value
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}/statement", response_model=None)
def account_statement(
    account_id: int,
    file_type: str = Query(default="json", pattern="^(json|csv|pdf)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
):
    account = get_account_or_404(db, account_id)
    if file_type == "csv":
        content = "account_number,balance,status\n"
        content += f"{account.account_number},{account.balance},{account.status}\n"
        return Response(content=content, media_type="text/csv")
    if file_type == "pdf":
        content = f"Mock PDF Statement\nAccount: {account.account_number}\nBalance: {account.balance}\n"
        return Response(content=content, media_type="application/pdf")
    return {"account": account.account_number, "balance": account.balance, "status": account.status}
