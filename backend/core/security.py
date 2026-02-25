"""
Security utilities: password hashing (bcrypt) and JWT encode/decode.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ── Password ───────────────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ────────────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"


def create_access_token(data: dict[str, Any]) -> str:
    """Create a signed JWT with expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT.
    Raises JWTError on invalid/expired tokens.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
