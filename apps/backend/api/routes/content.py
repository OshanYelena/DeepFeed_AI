"""
DeepFeed AI - Content Discovery Routes

Exposes the "Discover Now" manual-trigger endpoints. The hourly cron
continues to run automatically via Celery beat; these endpoints just
let an authenticated user kick off a personalized discovery on demand,
subject to per-user quota and cooldown.

POST /content/discover runs the whole pipeline synchronously (see
DiscoveryTriggerService's docstring for why) and only returns once it's
actually done, so the response already carries the final outcome —
there's no separate "wait for it to finish" step for callers to do.

Routes:
  POST /content/discover                   — run discovery+processing+ranking, return the outcome
  GET  /content/discover/status            — quota / next-cron / active-run / last-run
  GET  /content/discover/runs/{run_id}     — fetch a specific run by id
"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.schemas import error_response, success_response
from application.services.discovery_trigger_service import (
    CooldownActiveError,
    DiscoveryTriggerService,
    NoSearchPlanError,
    QuotaExceededError,
    _serialize_run,
)
from infrastructure.database.connection import get_db
from infrastructure.database.models import User

router = APIRouter(prefix="/content", tags=["Discovery"])


@router.post("/discover")
async def trigger_discovery(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kick off a personalized discovery run for the current user."""
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = DiscoveryTriggerService(db)

    try:
        run = await service.trigger(user_id=user_id, trace_id=trace_id)
        await db.commit()
    except QuotaExceededError as e:
        return error_response(
            code="DISCOVERY_QUOTA_EXCEEDED",
            message=str(e),
            trace_id=trace_id,
            details={
                "used": e.used,
                "limit": e.limit,
                "reset_at": e.reset_at.isoformat(),
            },
        )
    except CooldownActiveError as e:
        return error_response(
            code="DISCOVERY_COOLDOWN_ACTIVE",
            message=str(e),
            trace_id=trace_id,
            details={"seconds_remaining": e.seconds_remaining},
        )
    except NoSearchPlanError as e:
        return error_response(
            code="DISCOVERY_NO_SEARCH_PLAN",
            message=str(e),
            trace_id=trace_id,
        )

    return success_response(
        {
            "run_id": str(run.id),
            "task_id": run.task_id,
            "status": run.status,
            "new_items_count": run.new_items_count,
            "error_message": run.error_message,
            "queries": (run.search_queries or {}).get("queries", []),
        },
        trace_id,
    )


@router.get("/discover/status")
async def discovery_status(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Single-call payload powering the homepage status panel."""
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = DiscoveryTriggerService(db)
    status = await service.get_status(user_id=user_id)
    return success_response(status, trace_id)


@router.get("/discover/runs/{run_id}")
async def get_discovery_run(
    run_id: uuid.UUID,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Fetch one run by id — used by the frontend to poll an in-flight task."""
    trace_id = getattr(req.state, "trace_id", "")
    user_id = uuid.UUID(str(current_user.id))
    service = DiscoveryTriggerService(db)
    run = await service.get_run(user_id=user_id, run_id=run_id)
    if run is None:
        return error_response(
            code="DISCOVERY_RUN_NOT_FOUND",
            message=f"No discovery run with id {run_id}",
            trace_id=trace_id,
        )
    return success_response(_serialize_run(run), trace_id)
