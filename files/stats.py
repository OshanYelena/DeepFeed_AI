"""
DeepFeed AI - System Stats Routes
GET /admin/stats - System health metrics (admin only)
"""
import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from infrastructure.database.connection import get_db
from infrastructure.database.models import User, ContentItem, Recommendation, Feedback, AdaptationEvent
from api.dependencies.auth import get_admin_user
from api.schemas import success_response

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])


@router.get("")
async def get_system_stats(
    req: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")

    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0

    content_by_status = {}
    result = await db.execute(text("SELECT status, COUNT(*) as cnt FROM content_items GROUP BY status"))
    for row in result.all():
        content_by_status[row.status] = row.cnt

    rec_count = (await db.execute(select(func.count(Recommendation.id)))).scalar() or 0
    avg_score = (await db.execute(select(func.avg(Recommendation.final_score)))).scalar() or 0

    feedback_by_type = {}
    fb_result = await db.execute(text("SELECT feedback_type, COUNT(*) as cnt FROM feedback GROUP BY feedback_type"))
    for row in fb_result.all():
        feedback_by_type[row.feedback_type] = row.cnt

    adaptation_count = (await db.execute(select(func.count(AdaptationEvent.id)))).scalar() or 0

    return success_response({
        "users": {"total": user_count},
        "content": {"by_status": content_by_status, "total": sum(content_by_status.values())},
        "recommendations": {"total": rec_count, "avg_score": round(float(avg_score), 3)},
        "feedback": {"by_type": feedback_by_type},
        "adaptations": {"total": adaptation_count},
    }, trace_id)
