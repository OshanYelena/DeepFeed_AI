"""
DeepFeed AI - Agentic API Routes (M12-M15)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from infrastructure.database.connection import get_db
from infrastructure.database.models import (
    User, UserTopicPreference, SourcePreference, SearchPlan,
    AdaptationEvent, ReflectionReport, Source,
)
from api.dependencies.auth import get_current_user
from application.services.agents.research_planning_agent import ResearchPlanningAgent
from application.services.agents.adaptation_engine import AdaptationEngine, ReflectionAgent
from infrastructure.llm.providers import get_llm_provider
from api.schemas import success_response, error_response

router = APIRouter(prefix="/agent", tags=["Agentic"])


@router.get("/profile-insights")
async def get_profile_insights(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))

    strong_result = await db.execute(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == user_id, UserTopicPreference.weight >= 0.7)
        .order_by(UserTopicPreference.weight.desc()).limit(5)
    )
    strong = [p.topic for p in strong_result.scalars().all()]

    weak_result = await db.execute(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == user_id, UserTopicPreference.weight < 0.3)
        .limit(3)
    )
    weak = [p.topic for p in weak_result.scalars().all()]

    src_result = await db.execute(
        select(SourcePreference, Source.name)
        .join(Source)
        .where(SourcePreference.user_id == user_id)
        .order_by(SourcePreference.personal_trust_score.desc()).limit(5)
    )
    preferred_sources = [row[1] for row in src_result.all()]

    return success_response({
        "strong_interests": strong,
        "weak_interests": weak,
        "preferred_sources": preferred_sources,
    }, trace_id)


@router.get("/topic-preferences")
async def get_topic_preferences(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    result = await db.execute(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == user_id)
        .order_by(UserTopicPreference.weight.desc())
    )
    topics = [
        {"topic": p.topic, "weight": p.weight, "confidence": p.confidence, "source": p.source}
        for p in result.scalars().all()
    ]
    return success_response({"topics": topics}, trace_id)


class PreferenceCorrectionRequest(BaseModel):
    topic: str
    correction: str
    new_weight: float = 0.5


@router.post("/preferences/correct")
async def correct_preference(
    request: PreferenceCorrectionRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    result = await db.execute(
        select(UserTopicPreference).where(
            UserTopicPreference.user_id == user_id,
            UserTopicPreference.topic == request.topic,
        )
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.weight = request.new_weight
        pref.source = "explicit"
    else:
        pref = UserTopicPreference(
            user_id=user_id,
            topic=request.topic,
            weight=request.new_weight,
            source="explicit",
        )
        db.add(pref)
    await db.commit()
    return success_response({"message": "Preference updated", "topic": request.topic}, trace_id)


@router.post("/search-plan/generate")
async def generate_search_plan(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    llm = get_llm_provider("low")
    agent = ResearchPlanningAgent(db, llm)
    plan = await agent.generate_search_plan(user_id, trace_id)
    await db.commit()
    return success_response({
        "search_plan_id": str(plan.id),
        "queries": plan.queries.get("queries", []),
        "sources": plan.source_priorities.get("sources", []) if plan.source_priorities else [],
        "search_depth": plan.search_depth,
    }, trace_id)


@router.get("/search-plan")
async def get_search_plans(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    result = await db.execute(
        select(SearchPlan)
        .where(SearchPlan.user_id == user_id)
        .order_by(SearchPlan.created_at.desc()).limit(5)
    )
    plans = [
        {
            "id": str(p.id),
            "queries": p.queries.get("queries", []),
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in result.scalars().all()
    ]
    return success_response({"plans": plans}, trace_id)


class AdaptRunRequest(BaseModel):
    mode: str = "full"


@router.post("/adapt/run")
async def run_adaptation(
    request: AdaptRunRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    llm = get_llm_provider("medium")
    engine = AdaptationEngine(db, llm)
    result = await engine.run_full_cycle(user_id, trace_id)
    await db.commit()
    return success_response({"status": "completed", "summary": result}, trace_id)


@router.get("/adaptation-events")
async def get_adaptation_events(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    result = await db.execute(
        select(AdaptationEvent)
        .where(AdaptationEvent.user_id == user_id)
        .order_by(AdaptationEvent.created_at.desc()).limit(20)
    )
    events = [
        {
            "id": str(e.id),
            "agent": e.agent_name,
            "event_type": e.event_type,
            "decision": e.decision,
            "reason": e.reason,
            "confidence": e.confidence,
            "created_at": e.created_at.isoformat(),
        }
        for e in result.scalars().all()
    ]
    return success_response({"events": events}, trace_id)


@router.post("/reflection/run")
async def run_reflection(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    llm = get_llm_provider("large")
    agent = ReflectionAgent(db, llm)
    report = await agent.run(user_id, "daily", trace_id)
    await db.commit()
    return success_response({"report_id": str(report.id), "status": "completed"}, trace_id)


@router.get("/reflection/latest")
async def get_latest_reflection(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    result = await db.execute(
        select(ReflectionReport)
        .where(ReflectionReport.user_id == user_id)
        .order_by(ReflectionReport.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "No reflection reports yet", trace_id))
    return success_response({
        "id": str(report.id),
        "period": report.report_period,
        "insights": report.insights,
        "recommendations": report.recommendations_,
        "created_at": report.created_at.isoformat(),
    }, trace_id)
