"""
DeepFeed AI - Auth Application Service
Handles user registration and authentication.
Business logic is here — NOT in routes or models.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import User, UserProfile
from infrastructure.auth.passwords import hash_password, verify_password
from infrastructure.auth.tokens import create_access_token, create_refresh_token, decode_token
from application.dtos.user_dtos import RegisterRequest, LoginRequest
from logger import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, request: RegisterRequest, trace_id: str) -> User:
        """Register a new user. Raises ValueError if email already exists."""
        logger.info("user_registration_attempt", email=request.email, trace_id=trace_id)

        # Check duplicate
        existing = await self._db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            logger.warning("registration_duplicate_email", email=request.email, trace_id=trace_id)
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            role="user",
        )
        self._db.add(user)
        await self._db.flush()  # Get ID before creating profile

        # Create default profile
        profile = UserProfile(user_id=user.id)
        self._db.add(profile)

        logger.info("user_registered", user_id=str(user.id), trace_id=trace_id)
        return user

    async def login(self, request: LoginRequest, trace_id: str) -> tuple[str, str]:
        """Authenticate user. Returns (access_token, refresh_token)."""
        logger.info("login_attempt", email=request.email, trace_id=trace_id)

        result = await self._db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            logger.warning("login_failed", email=request.email, trace_id=trace_id)
            raise ValueError("Invalid email or password")

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id))

        logger.info("login_success", user_id=str(user.id), trace_id=trace_id)
        return access_token, refresh_token

    async def refresh(self, refresh_token: str, trace_id: str) -> str:
        """Exchange a valid refresh token for a new access token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            logger.warning("refresh_rejected", reason="invalid_or_wrong_type", trace_id=trace_id)
            raise ValueError("Invalid or expired refresh token")

        result = await self._db.execute(
            select(User).where(User.id == uuid.UUID(payload["sub"]))
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("refresh_rejected", reason="user_not_found", trace_id=trace_id)
            raise ValueError("Invalid or expired refresh token")

        access_token = create_access_token(str(user.id), user.role)
        logger.info("token_refreshed", user_id=str(user.id), trace_id=trace_id)
        return access_token
