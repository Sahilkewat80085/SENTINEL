from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token for a subject (usually username or user ID)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> str | None:
    """Decodes a JWT access token and returns the subject (sub) or None if invalid/expired."""
    try:
        decoded_payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return decoded_payload.get("sub")
    except jwt.PyJWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Computes a bcrypt hash for a plain text password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

