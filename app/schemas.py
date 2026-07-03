from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.CUSTOMER


class UserRead(ReadModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    role: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OtpRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern="^(email_verification|password_reset|mfa)$")


class OtpVerify(BaseModel):
    email: EmailStr
    purpose: str
    code: str = Field(min_length=4, max_length=8)


class PasswordReset(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=72)


class MfaToggle(BaseModel):
    enabled: bool


class MfaLogin(BaseModel):
    email: EmailStr
    password: str
    code: str = Field(min_length=4, max_length=8)


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    pan_number: str | None = None
    aadhaar_last_four: str | None = Field(default=None, min_length=4, max_length=4)


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    status: CustomerStatus | None = None
    kyc_status: str | None = None


class CustomerRead(ReadModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    status: str
    kyc_status: str
    created_at: datetime


class AddressCreate(BaseModel):
    address_type: str = "home"
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str = "India"


class AddressRead(AddressCreate, ReadModel):
    id: int
    customer_id: int


class NomineeCreate(BaseModel):
    full_name: str
    relationship: str
    phone: str | None = None
    share_percent: Decimal = Decimal("100.00")


class NomineeRead(NomineeCreate, ReadModel):
    id: int
    customer_id: int


class DocumentCreate(BaseModel):
    document_type: str
    file_name: str
    file_path: str


class DocumentRead(DocumentCreate, ReadModel):
    id: int
    customer_id: int
    verified: bool


class AccountCreate(BaseModel):
    customer_id: int
    account_type: AccountType = AccountType.SAVINGS
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    interest_rate: Decimal | None = None
    maturity_date: date | None = None
    joint_holder_customer_id: int | None = None


class AccountStatusUpdate(BaseModel):
    status: AccountStatus


class AccountRead(ReadModel):
    id: int
    customer_id: int
    account_number: str
    account_type: str
    status: str
    balance: Decimal
    created_at: datetime


class DepositRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    description: str | None = None


class WithdrawalRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    description: str | None = None


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0)
    transaction_type: TransactionType = TransactionType.FUND_TRANSFER
    description: str | None = None


class ScheduledTransferRequest(TransferRequest):
    scheduled_for: datetime


class TransactionRead(ReadModel):
    id: int
    reference_no: str
    from_account_id: int | None
    to_account_id: int | None
    transaction_type: str
    channel: str
    amount: Decimal
    status: str
    description: str | None
    scheduled_for: datetime | None
    created_at: datetime


class BeneficiaryCreate(BaseModel):
    customer_id: int
    name: str
    bank_name: str
    account_number: str
    ifsc_code: str
    nickname: str | None = None


class BeneficiaryRead(BeneficiaryCreate, ReadModel):
    id: int


class LoanCreate(BaseModel):
    customer_id: int
    loan_type: LoanType
    amount: Decimal = Field(gt=0)
    annual_interest_rate: Decimal = Field(gt=0)
    tenure_months: int = Field(gt=0)


class LoanDecision(BaseModel):
    status: LoanStatus


class LoanRead(ReadModel):
    id: int
    customer_id: int
    loan_type: str
    amount: Decimal
    annual_interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    status: str


class CardCreate(BaseModel):
    account_id: int
    customer_id: int
    card_type: CardType = CardType.DEBIT
    daily_limit: Decimal = Decimal("25000.00")
    monthly_limit: Decimal = Decimal("250000.00")


class PinCreate(BaseModel):
    pin: str = Field(min_length=4, max_length=6)


class CardLimitUpdate(BaseModel):
    daily_limit: Decimal | None = None
    monthly_limit: Decimal | None = None


class CardRead(ReadModel):
    id: int
    account_id: int
    customer_id: int
    card_type: str
    last_four: str
    status: str
    daily_limit: Decimal
    monthly_limit: Decimal


class BranchCreate(BaseModel):
    code: str
    name: str
    ifsc_code: str
    address: str
    city: str
    state: str
    manager_user_id: int | None = None


class BranchRead(BranchCreate, ReadModel):
    id: int


class EmployeeCreate(BaseModel):
    branch_id: int
    full_name: str
    email: EmailStr
    designation: str
    salary: Decimal


class EmployeeRead(EmployeeCreate, ReadModel):
    id: int
    is_active: bool


class AttendanceCreate(BaseModel):
    employee_id: int
    work_date: date
    status: str


class LeaveCreate(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    reason: str


class PayrollCreate(BaseModel):
    employee_id: int
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    gross_pay: Decimal
    deductions: Decimal = Decimal("0.00")


class NotificationCreate(BaseModel):
    user_id: int | None = None
    customer_id: int | None = None
    channel: str = Field(pattern="^(email|sms|push|in_app)$")
    subject: str
    message: str


class NotificationRead(NotificationCreate, ReadModel):
    id: int
    read_at: datetime | None
