"""
DeepFeed AI - JWT Token Utilities
Access tokens (15min) and refresh tokens (30 days) as per TDS §15.2
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from config import settings
from logger import get_logger

logger = get_logger(__name__)


def create_access_token(subject: str, role: str = "user") -> str:
    """Create a short-lived access JWT."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh JWT."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns payload or None on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        return None


def verify_access_token(token: str) -> Optional[str]:
    """Verify access token and return user_id (sub) or None."""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload.get("sub")
    return None
