"""
DeepFeed AI - Password Security
Argon2 password hashing as specified in TDS §15.5
Minimum 12 characters, strong complexity enforced at validation layer.
"""
from passlib.context import CryptContext

# Use Argon2 as primary, bcrypt as fallback (TDS §15.5)
_pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain text password."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)
