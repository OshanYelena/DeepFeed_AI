"""
DeepFeed AI - Profile Routes (M2) & Interest Routes (M3)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from infrastructure.database.models import User
from api.dependencies.auth import get_current_user
from application.services.profile_service import ProfileService, InterestService
from application.dtos.user_dtos import (
    UpdateProfileRequest, ProfileResponse,
    CreateInterestRequest, UpdateInterestRequest, InterestResponse,
)
from api.schemas import success_response, error_response

profile_router = APIRouter(prefix="/profile", tags=["Profile"])
interests_router = APIRouter(prefix="/interests", tags=["Interests"])


# ── Profile ───────────────────────────────────────────────────────────────────

@profile_router.get("/me")
async def get_profile(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = ProfileService(db)
    profile = await service.get_profile(current_user.id, trace_id)
    if not profile:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Profile not found", trace_id))
    return success_response(ProfileResponse.model_validate(profile).model_dump(), trace_id)


@profile_router.put("/me")
async def update_profile(
    request: UpdateProfileRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = ProfileService(db)
    profile = await service.update_profile(current_user.id, request, trace_id)
    await db.commit()
    return success_response(ProfileResponse.model_validate(profile).model_dump(), trace_id)


# ── Interests ─────────────────────────────────────────────────────────────────

@interests_router.post("", status_code=status.HTTP_201_CREATED)
async def create_interest(
    request: CreateInterestRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = InterestService(db)
    # Ensure we pass a plain UUID, not a SQLAlchemy column expression
    user_id = uuid.UUID(str(current_user.id))
    interest = await service.create_interest(user_id, request, trace_id)
    await db.commit()
    return success_response(InterestResponse.model_validate(interest).model_dump(), trace_id)


@interests_router.get("")
async def list_interests(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = InterestService(db)
    user_id = uuid.UUID(str(current_user.id))
    interests = await service.list_interests(user_id, trace_id)
    return success_response(
        [InterestResponse.model_validate(i).model_dump() for i in interests],
        trace_id,
    )


@interests_router.put("/{interest_id}")
async def update_interest(
    interest_id: uuid.UUID,
    request: UpdateInterestRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = InterestService(db)
    user_id = uuid.UUID(str(current_user.id))
    try:
        interest = await service.update_interest(user_id, interest_id, request, trace_id)
        await db.commit()
        return success_response(InterestResponse.model_validate(interest).model_dump(), trace_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", str(e), trace_id))


@interests_router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interest(
    interest_id: uuid.UUID,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    trace_id = getattr(req.state, "trace_id", "")
    service = InterestService(db)
    user_id = uuid.UUID(str(current_user.id))
    try:
        await service.delete_interest(user_id, interest_id, trace_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", str(e), trace_id))
