"""
DeepFeed AI - Feed Routes (M9)
GET /feed
GET /feed/{recommendation_id}
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from infrastructure.database.models import User
from api.dependencies.auth import get_current_user
from application.services.feed_service import FeedService
from api.schemas import success_response, error_response

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get("")
async def get_feed(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    content_type: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = FeedService(db)
    items = await service.get_feed(
        user_id, limit=limit, offset=offset,
        content_type=content_type, min_score=min_score, trace_id=trace_id,
    )
    return success_response({"items": items, "limit": limit, "offset": offset}, trace_id)


@router.get("/{recommendation_id}")
async def get_recommendation_detail(
    recommendation_id: uuid.UUID,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = FeedService(db)
    detail = await service.get_recommendation_detail(user_id, recommendation_id, trace_id)
    if not detail:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Recommendation not found", trace_id))
    return success_response(detail, trace_id)
