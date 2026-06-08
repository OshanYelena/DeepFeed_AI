"""
DeepFeed AI - Profile & Interest Application Services
Handles profile management (M2) and interest management (M3).
All writes go through these services - never direct model manipulation.
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import User, UserProfile, Interest
from application.dtos.user_dtos import UpdateProfileRequest, CreateInterestRequest, UpdateInterestRequest
from logger import get_logger

logger = get_logger(__name__)


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_profile(self, user_id: uuid.UUID, trace_id: str) -> Optional[UserProfile]:
        result = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        user_id: uuid.UUID,
        request: UpdateProfileRequest,
        trace_id: str,
    ) -> UserProfile:
        logger.info("profile_update", user_id=str(user_id), trace_id=trace_id)

        result = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            # Create profile if missing
            profile = UserProfile(user_id=user_id)
            self._db.add(profile)

        if request.expertise_level is not None:
            profile.expertise_level = request.expertise_level
        if request.preferred_depth is not None:
            profile.preferred_depth = request.preferred_depth
        if request.preferred_frequency is not None:
            profile.preferred_frequency = request.preferred_frequency

        logger.info("profile_updated", user_id=str(user_id), trace_id=trace_id)
        return profile


class InterestService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_interest(
        self,
        user_id: uuid.UUID,
        request: CreateInterestRequest,
        trace_id: str,
    ) -> Interest:
        logger.info("interest_create", user_id=str(user_id), name=request.name, trace_id=trace_id)

        interest = Interest(
            user_id=user_id,
            name=request.name,
            description=request.description,
            weight=request.weight,
        )
        self._db.add(interest)
        await self._db.flush()

        logger.info("interest_created", interest_id=str(interest.id), trace_id=trace_id)
        return interest

    async def list_interests(self, user_id: uuid.UUID, trace_id: str) -> List[Interest]:
        result = await self._db.execute(
            select(Interest)
            .where(Interest.user_id == user_id)
            .order_by(Interest.weight.desc())
        )
        return list(result.scalars().all())

    async def update_interest(
        self,
        user_id: uuid.UUID,
        interest_id: uuid.UUID,
        request: UpdateInterestRequest,
        trace_id: str,
    ) -> Interest:
        interest = await self._get_user_interest(user_id, interest_id)

        if request.name is not None:
            interest.name = request.name
        if request.description is not None:
            interest.description = request.description
        if request.weight is not None:
            interest.weight = request.weight

        logger.info("interest_updated", interest_id=str(interest_id), trace_id=trace_id)
        return interest

    async def delete_interest(
        self,
        user_id: uuid.UUID,
        interest_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        interest = await self._get_user_interest(user_id, interest_id)
        await self._db.delete(interest)
        logger.info("interest_deleted", interest_id=str(interest_id), trace_id=trace_id)

    async def _get_user_interest(self, user_id: uuid.UUID, interest_id: uuid.UUID) -> Interest:
        result = await self._db.execute(
            select(Interest).where(
                Interest.id == interest_id,
                Interest.user_id == user_id,
            )
        )
        interest = result.scalar_one_or_none()
        if not interest:
            raise ValueError(f"Interest {interest_id} not found")
        return interest
