import secrets
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings


settings = get_settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    password_digest = sha256(password.encode("utf-8")).digest()
    return bcrypt.hashpw(password_digest, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_digest = sha256(plain_password.encode("utf-8")).digest()
    return bcrypt.checkpw(password_digest, hashed_password.encode("utf-8"))


def new_token_id() -> str:
    return uuid4().hex


def create_access_token(user_id: int, role: str) -> str:
    expires_at = utc_now() + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expires_at,
        "iat": utc_now(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, token_id: str) -> str:
    expires_at = utc_now() + timedelta(days=settings.refresh_token_days)
    payload = {
        "sub": str(user_id),
        "jti": token_id,
        "type": "refresh",
        "exp": expires_at,
        "iat": utc_now(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    return payload


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_card_last_four() -> str:
    return f"{secrets.randbelow(10_000):04d}"


def generate_reference(prefix: str) -> str:
    return f"{prefix}-{utc_now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
