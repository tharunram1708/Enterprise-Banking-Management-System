from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.core.constants import (
    AccountStatus,
    AccountType,
    CardStatus,
    CardType,
    CustomerStatus,
    LoanStatus,
    LoanType,
    TransactionStatus,
    TransactionType,
    UserRole,
)
from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.CUSTOMER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(120))
    failed_login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list["UserSession"]] = orm_relationship(back_populates="user")


class UserSession(TimestampMixin, Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    refresh_token_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = orm_relationship(back_populates="sessions")


class VerificationCode(TimestampMixin, Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)


class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(80))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    pan_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    aadhaar_last_four: Mapped[str | None] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(30), default=CustomerStatus.PENDING.value, nullable=False)
    kyc_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    addresses: Mapped[list["Address"]] = orm_relationship(back_populates="customer", cascade="all, delete-orphan")
    nominees: Mapped[list["Nominee"]] = orm_relationship(back_populates="customer", cascade="all, delete-orphan")
    documents: Mapped[list["CustomerDocument"]] = orm_relationship(back_populates="customer", cascade="all, delete-orphan")
    accounts: Mapped[list["Account"]] = orm_relationship(
        back_populates="customer",
        foreign_keys="Account.customer_id",
    )


class Address(TimestampMixin, Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    address_type: Mapped[str] = mapped_column(String(30), default="home", nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(80), default="India", nullable=False)

    customer: Mapped[Customer] = orm_relationship(back_populates="addresses")


class Nominee(TimestampMixin, Base):
    __tablename__ = "nominees"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship: Mapped[str] = mapped_column(String(60), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    share_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("100.00"), nullable=False)

    customer: Mapped[Customer] = orm_relationship(back_populates="nominees")


class CustomerDocument(TimestampMixin, Base):
    __tablename__ = "customer_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(60), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Customer] = orm_relationship(back_populates="documents")


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    account_number: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(40), default=AccountType.SAVINGS.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=AccountStatus.ACTIVE.value, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    maturity_date: Mapped[date | None] = mapped_column(Date)
    joint_holder_customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))

    customer: Mapped[Customer] = orm_relationship(foreign_keys=[customer_id], back_populates="accounts")


class Beneficiary(TimestampMixin, Base):
    __tablename__ = "beneficiaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_number: Mapped[str] = mapped_column(String(24), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(80))


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_no: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=TransactionStatus.SUCCESS.value, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Loan(TimestampMixin, Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    loan_type: Mapped[str] = mapped_column(String(40), default=LoanType.PERSONAL.value, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tenure_months: Mapped[int] = mapped_column(nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=LoanStatus.APPLIED.value, nullable=False)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoanRepaymentSchedule(Base):
    __tablename__ = "loan_repayment_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False)
    installment_no: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date | None] = mapped_column(Date)


class Card(TimestampMixin, Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    card_type: Mapped[str] = mapped_column(String(30), default=CardType.DEBIT.value, nullable=False)
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=CardStatus.ACTIVE.value, nullable=False)
    pin_hash: Mapped[str | None] = mapped_column(String(255))
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("25000.00"), nullable=False)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("250000.00"), nullable=False)


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    manager_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(80), nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class LeaveRequest(TimestampMixin, Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)


class Payroll(Base):
    __tablename__ = "payroll"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date | None] = mapped_column(Date)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
