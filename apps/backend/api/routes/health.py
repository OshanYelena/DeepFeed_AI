"""
DeepFeed AI - Health Routes (Phase 0)
GET /health         - Basic liveness
GET /health/ready   - Readiness: DB + Queue + LLM checks
"""
from fastapi import APIRouter, Request
from infrastructure.database.connection import check_database_health
from infrastructure.llm.providers import get_llm_router
from api.schemas import success_response

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health(req: Request) -> dict:
    trace_id = getattr(req.state, "trace_id", "")
    return success_response({"status": "ok", "service": "deepfeed-ai"}, trace_id)


@router.get("/ready")
async def readiness(req: Request) -> dict:
    trace_id = getattr(req.state, "trace_id", "")

    db_ok = await check_database_health()
    llm_configured = get_llm_router().is_available()

    all_ok = db_ok

    return success_response({
        "status": "ready" if all_ok else "degraded",
        "checks": {
            "database": "ok" if db_ok else "failed",
            "llm_provider": "configured" if llm_configured else "not_configured",
        },
    }, trace_id)
