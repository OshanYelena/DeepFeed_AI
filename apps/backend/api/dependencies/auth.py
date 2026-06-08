"""
DeepFeed AI - Auth Dependencies
FastAPI dependency injection for JWT-protected routes.
"""
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.connection import get_db
from infrastructure.database.models import User
from infrastructure.auth.tokens import verify_access_token
from sqlalchemy import select
from logger import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate the authenticated user from the JWT."""
    user_id = verify_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
