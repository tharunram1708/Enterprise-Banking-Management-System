from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.constants import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_password,
    new_token_id,
    utc_now,
    verify_password,
)
from app.db.session import get_db
from app.models import LoginHistory, User, UserSession, VerificationCode
from app.schemas import (
    Message,
    MfaLogin,
    MfaToggle,
    OtpRequest,
    OtpVerify,
    PasswordReset,
    RefreshTokenRequest,
    TokenPair,
    UserCreate,
    UserRead,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


def client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def is_locked(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > utc_now())


def write_login_history(
    db: Session,
    email: str,
    request: Request,
    success: bool,
    user_id: int | None = None,
    reason: str | None = None,
) -> None:
    db.add(
        LoginHistory(
            user_id=user_id,
            email=email,
            ip_address=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            success=success,
            reason=reason,
            created_at=utc_now(),
        )
    )


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def issue_tokens(db: Session, user: User, request: Request) -> TokenPair:
    refresh_id = new_token_id()
    refresh_expires_at = utc_now() + timedelta(days=settings.refresh_token_days)

    db.add(
        UserSession(
            user_id=user.id,
            refresh_token_id=refresh_id,
            ip_address=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            expires_at=refresh_expires_at,
        )
    )
    db.commit()

    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, refresh_id),
    )


def verify_otp_record(db: Session, email: str, purpose: str, code: str) -> VerificationCode:
    record = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.email == email.lower(),
            VerificationCode.purpose == purpose,
            VerificationCode.used_at.is_(None),
            VerificationCode.expires_at > utc_now(),
        )
        .order_by(VerificationCode.id.desc())
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is invalid or expired")

    record.attempts += 1
    if not verify_password(code, record.code_hash):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is invalid or expired")

    record.used_at = utc_now()
    db.commit()
    db.refresh(record)
    return record


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    email = payload.email.lower()
    if find_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user_count = db.scalar(select(func.count(User.id))) or 0
    role = UserRole.ADMIN.value if user_count == 0 else UserRole.CUSTOMER.value

    user = User(
        email=email,
        full_name=payload.full_name,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenPair:
    email = form.username.lower()
    user = find_user_by_email(db, email)

    if not user:
        write_login_history(db, email, request, False, reason="user_not_found")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if is_locked(user):
        write_login_history(db, email, request, False, user.id, "account_locked")
        db.commit()
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked")

    if not verify_password(form.password, user.hashed_password):
        user.failed_login_count += 1
        if user.failed_login_count >= settings.max_login_attempts:
            user.locked_until = utc_now() + timedelta(minutes=settings.account_lock_minutes)
        write_login_history(db, email, request, False, user.id, "bad_password")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.mfa_enabled:
        write_login_history(db, email, request, False, user.id, "mfa_required")
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA code required")

    user.failed_login_count = 0
    user.locked_until = None
    write_login_history(db, email, request, True, user.id)
    return issue_tokens(db, user, request)


@router.post("/mfa-login", response_model=TokenPair)
def mfa_login(payload: MfaLogin, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = find_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    verify_otp_record(db, payload.email, "mfa", payload.code)
    user.failed_login_count = 0
    user.locked_until = None
    write_login_history(db, payload.email.lower(), request, True, user.id)
    return issue_tokens(db, user, request)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    token_data = decode_token(payload.refresh_token, expected_type="refresh")
    session = db.scalar(
        select(UserSession).where(
            UserSession.refresh_token_id == token_data["jti"],
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now(),
        )
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is not active")

    user = db.get(User, int(token_data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")

    session.revoked_at = utc_now()
    return issue_tokens(db, user, request)


@router.post("/logout", response_model=Message)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> Message:
    token_data = decode_token(payload.refresh_token, expected_type="refresh")
    session = db.scalar(select(UserSession).where(UserSession.refresh_token_id == token_data["jti"]))
    if session and not session.revoked_at:
        session.revoked_at = utc_now()
        db.commit()
    return Message(message="Logged out")


@router.post("/otp/request", response_model=Message)
def request_otp(payload: OtpRequest, db: Session = Depends(get_db)) -> Message:
    user = find_user_by_email(db, payload.email)
    code = generate_otp()
    expires_at = utc_now() + timedelta(minutes=settings.otp_expire_minutes)

    db.add(
        VerificationCode(
            user_id=user.id if user else None,
            email=payload.email.lower(),
            purpose=payload.purpose,
            code_hash=hash_password(code),
            expires_at=expires_at,
        )
    )
    db.commit()
    return Message(message=f"OTP generated. Mock delivery code: {code}")


@router.post("/otp/verify", response_model=Message)
def verify_otp(payload: OtpVerify, db: Session = Depends(get_db)) -> Message:
    record = verify_otp_record(db, payload.email, payload.purpose, payload.code)

    if payload.purpose == "email_verification" and record.user_id:
        user = db.get(User, record.user_id)
        if user:
            user.is_verified = True
            db.commit()

    return Message(message="OTP verified")


@router.post("/forgot-password", response_model=Message)
def forgot_password(payload: OtpRequest, db: Session = Depends(get_db)) -> Message:
    payload.purpose = "password_reset"
    return request_otp(payload, db)


@router.post("/reset-password", response_model=Message)
def reset_password(payload: PasswordReset, db: Session = Depends(get_db)) -> Message:
    user = find_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    verify_otp_record(db, payload.email, "password_reset", payload.code)
    user.hashed_password = hash_password(payload.new_password)
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()
    return Message(message="Password reset successful")


@router.post("/mfa", response_model=Message)
def update_mfa(payload: MfaToggle, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Message:
    current_user.mfa_enabled = payload.enabled
    current_user.mfa_secret = new_token_id() if payload.enabled else None
    db.commit()
    return Message(message="MFA setting updated")


@router.get("/me", response_model=UserRead)
def read_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user
