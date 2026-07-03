from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"


class CustomerStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    INACTIVE = "inactive"


class AccountType(StrEnum):
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class TransactionType(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    FUND_TRANSFER = "fund_transfer"
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"


class TransactionStatus(StrEnum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class LoanType(StrEnum):
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    EDUCATION = "education"
    BUSINESS = "business"


class LoanStatus(StrEnum):
    APPLIED = "applied"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    CLOSED = "closed"


class CardType(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class CardStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"
