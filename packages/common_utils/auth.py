"""JWT helpers.

SECURITY: no fallback secret. If JWT_SECRET_KEY is not set, importing this
module raises. This file is currently imported by nothing; when auth is wired,
set the secret in the environment.

Dependencies (`python-jose`, `passlib[bcrypt]`) are intentionally NOT in any
service requirements yet, because no service uses this module. Add them in the
same change that wires auth — do not ship an import that fails at runtime.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone


def _secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured; refusing to start with an "
            "implicit secret."
        )
    return secret


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    from jose import jwt  # imported lazily: optional dependency

    to_encode = dict(data)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    from jose import JWTError, jwt  # imported lazily: optional dependency

    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext

    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    from passlib.context import CryptContext

    return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(
        plain_password, hashed_password
    )
