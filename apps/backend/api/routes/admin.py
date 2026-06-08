"""
DeepFeed AI - Feedback Routes (M11) & Admin Routes
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from infrastructure.database.models import User
from api.dependencies.auth import get_current_user, get_admin_user
from application.services.feedback_service import FeedbackService
from application.services.discovery_service import SourceService
from api.schemas import success_response, error_response

feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    recommendation_id: uuid.UUID
    feedback_type: str

    @field_validator("feedback_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("like", "dislike", "bookmark", "ignore", "read"):
            raise ValueError("Invalid feedback_type")
        return v


class ReadEventRequest(BaseModel):
    recommendation_id: uuid.UUID
    duration_seconds: int


@feedback_router.post("", status_code=status.HTTP_201_CREATED)
async def record_feedback(
    request: FeedbackRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = FeedbackService(db)
    try:
        await service.record_feedback(user_id, request.recommendation_id, request.feedback_type, trace_id)
        await db.commit()
        return success_response({"message": "Feedback recorded successfully"}, trace_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("VALIDATION_ERROR", str(e), trace_id))


@feedback_router.post("/read", status_code=status.HTTP_201_CREATED)
async def record_read(
    request: ReadEventRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = FeedbackService(db)
    await service.record_read_event(user_id, request.recommendation_id, request.duration_seconds, trace_id)
    await db.commit()
    return success_response({"message": "Read event recorded"}, trace_id)


# ── Admin Sources ─────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateSourceRequest(BaseModel):
    name: str
    source_type: str
    base_url: str
    trust_score: float = 0.7

    @field_validator("source_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("rss", "arxiv", "blog", "github", "docs"):
            raise ValueError("Invalid source_type")
        return v


class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    trust_score: Optional[float] = None
    is_active: Optional[bool] = None


@admin_router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(
    request: CreateSourceRequest,
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = SourceService(db)
    source = await service.create_source(
        request.name, request.source_type, request.base_url, request.trust_score, trace_id
    )
    await db.commit()
    return success_response({"source_id": str(source.id), "name": source.name}, trace_id)


@admin_router.get("/sources")
async def list_sources(
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = SourceService(db)
    sources = await service.list_sources(active_only=False)
    data = [
        {
            "id": str(s.id),
            "name": s.name,
            "source_type": s.source_type,
            "base_url": s.base_url,
            "trust_score": s.trust_score,
            "is_active": s.is_active,
        }
        for s in sources
    ]
    return success_response(data, trace_id)


@admin_router.put("/sources/{source_id}")
async def update_source(
    source_id: uuid.UUID,
    request: UpdateSourceRequest,
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    service = SourceService(db)
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    try:
        source = await service.update_source(source_id, **updates)
        await db.commit()
        return success_response({"source_id": str(source.id), "updated": True}, trace_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", str(e), trace_id))


@admin_router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_source(
    source_id: uuid.UUID,
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    trace_id = getattr(req.state, "trace_id", "")
    service = SourceService(db)
    try:
        await service.disable_source(source_id, trace_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", str(e), trace_id))


@admin_router.post("/jobs/discovery/run")
async def run_discovery(
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from application.services.discovery_service import DiscoveryService
    trace_id = getattr(req.state, "trace_id", "")
    service = DiscoveryService(db)
    new_items = await service.run_discovery(trace_id=trace_id)
    await db.commit()
    return success_response({"job_id": str(uuid.uuid4()), "new_items_discovered": new_items}, trace_id)
