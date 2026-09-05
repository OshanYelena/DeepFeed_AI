"""
DeepFeed AI - Discovery Trigger Service

Handles the "Discover Now" button: enforces per-user quota, resolves the
user's latest search plan, records the run, and runs the pipeline.

Runs discovery -> processing -> ranking synchronously, in-request, instead
of dispatching to Celery. That's a deliberate trade-off, not an oversight:
in this deployment the worker container gets restarted independently of
the API (observed twice), and task_acks_late redelivery didn't recover the
in-flight task either time — the DiscoveryRun row was left "running"
forever with nothing left to ever mark it terminal. A blocking request is
slower but fails honestly (the HTTP call itself errors out) instead of
silently losing work. Revisit if/when the worker's uptime is solid.

Separated from DiscoveryService because that service is the worker-side
worker; this service is the API-side gatekeeper.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.database.models import (
    DiscoveryRun,
    Interest,
    SearchPlan,
)
from logger import get_logger

logger = get_logger(__name__)


# Sentinel exceptions — the route layer catches these and maps to HTTP codes.
class QuotaExceededError(Exception):
    def __init__(self, used: int, limit: int, reset_at: datetime) -> None:
        self.used = used
        self.limit = limit
        self.reset_at = reset_at
        super().__init__(f"Daily discovery quota exhausted: {used}/{limit}")


class CooldownActiveError(Exception):
    def __init__(self, seconds_remaining: int) -> None:
        self.seconds_remaining = seconds_remaining
        super().__init__(f"Cooldown active: {seconds_remaining}s remaining")


class NoSearchPlanError(Exception):
    """User asked for personalized discovery but has no search plan yet."""


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# Celery task's own time_limit (420s) plus a buffer. A run stuck in
# pending/running past this point means the worker died mid-task (a
# restart, an OOM kill) rather than the task's own except block ever
# running — nothing will ever mark that row terminal on its own, and the
# frontend would poll it forever. Self-heal here instead.
STALE_RUN_THRESHOLD_SECONDS = 600


class DiscoveryTriggerService:
    """API-side coordinator for manual discovery triggers."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Quota & cooldown ─────────────────────────────────────────────────────

    async def _count_runs_last_24h(self, user_id: uuid.UUID) -> int:
        cutoff = _now_utc() - timedelta(hours=24)
        stmt = (
            select(func.count(DiscoveryRun.id))
            .where(DiscoveryRun.user_id == user_id)
            .where(DiscoveryRun.started_at >= cutoff)
        )
        result = await self._db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def _earliest_run_in_window(
        self, user_id: uuid.UUID
    ) -> Optional[datetime]:
        """When does the user's oldest run-in-window age out? That's when the
        quota effectively resets to N-1 instead of N. For UX simplicity we
        return that timestamp as 'reset_at' even though it's technically a
        rolling window."""
        cutoff = _now_utc() - timedelta(hours=24)
        stmt = (
            select(func.min(DiscoveryRun.started_at))
            .where(DiscoveryRun.user_id == user_id)
            .where(DiscoveryRun.started_at >= cutoff)
        )
        result = await self._db.execute(stmt)
        earliest = result.scalar_one_or_none()
        return earliest

    async def _seconds_since_last_run(
        self, user_id: uuid.UUID
    ) -> Optional[float]:
        stmt = (
            select(DiscoveryRun.started_at)
            .where(DiscoveryRun.user_id == user_id)
            .order_by(DiscoveryRun.started_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        last = result.scalar_one_or_none()
        if last is None:
            return None
        return (_now_utc() - last).total_seconds()

    # ── Search plan resolution ───────────────────────────────────────────────

    async def _latest_search_plan(self, user_id: uuid.UUID) -> Optional[SearchPlan]:
        stmt = (
            select(SearchPlan)
            .where(SearchPlan.user_id == user_id)
            .order_by(SearchPlan.created_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _plan_queries(plan: Optional[SearchPlan]) -> List[str]:
        """Extract the query list from a search plan.

        SearchPlan.queries is a JSON dict like {"queries": ["...", "..."]}.
        We tolerate missing or malformed payloads — the caller decides what
        to do when the list is empty."""
        if plan is None:
            return []
        payload = plan.queries or {}
        queries = payload.get("queries") or []
        # Tolerate a bare list of strings under the root, too.
        if not queries and isinstance(payload, list):
            queries = payload
        return [q for q in queries if isinstance(q, str) and q.strip()]

    async def _has_interests_added_since(self, user_id: uuid.UUID, since: datetime) -> bool:
        """True if the user has added an interest since `since`.

        generate_search_plan() builds its queries from the user's interests
        at the moment it runs — it doesn't re-read them later. Without this
        check, a plan generated before someone adds a new interest (or
        finishes onboarding with none yet) gets reused by every future
        Discover Now click forever, so the new interest is silently never
        searched for. Weight/description edits don't need a new plan —
        generate_search_plan only uses interest *names* — so this only
        looks for newly created rows, not changed ones.
        """
        stmt = select(func.count()).select_from(Interest).where(
            Interest.user_id == user_id, Interest.created_at > since
        )
        result = await self._db.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def _reap_if_stale(self, run: Optional[DiscoveryRun]) -> Optional[DiscoveryRun]:
        """Flip a run stuck past STALE_RUN_THRESHOLD_SECONDS to 'failed' so
        it doesn't sit as 'active' forever. See threshold comment above."""
        if run is None or run.status not in ("pending", "running"):
            return run
        age_seconds = (_now_utc() - run.started_at).total_seconds()
        if age_seconds < STALE_RUN_THRESHOLD_SECONDS:
            return run
        run.status = "failed"
        run.error_message = "Lost contact with the background worker. Try again."
        run.completed_at = _now_utc()
        await self._db.commit()
        logger.warning(
            "discovery_run_reaped_as_stale",
            run_id=str(run.id),
            age_seconds=int(age_seconds),
        )
        return run

    # ── Public API ───────────────────────────────────────────────────────────

    async def get_status(self, user_id: uuid.UUID) -> dict:
        """Single endpoint payload — everything the UI needs to render the
        status panel and decide whether the button is clickable."""
        used = await self._count_runs_last_24h(user_id)
        limit = settings.discovery_manual_daily_limit

        # Last completed run for "last discovered X ago" copy
        last_completed_stmt = (
            select(DiscoveryRun)
            .where(DiscoveryRun.user_id == user_id)
            .where(DiscoveryRun.status == "completed")
            .order_by(DiscoveryRun.completed_at.desc())
            .limit(1)
        )
        last_completed = (
            await self._db.execute(last_completed_stmt)
        ).scalar_one_or_none()

        # Active run (if any) — at most one per user normally; we return the most
        # recent non-terminal row.
        active_stmt = (
            select(DiscoveryRun)
            .where(DiscoveryRun.user_id == user_id)
            .where(DiscoveryRun.status.in_(["pending", "running"]))
            .order_by(DiscoveryRun.started_at.desc())
            .limit(1)
        )
        active = (await self._db.execute(active_stmt)).scalar_one_or_none()
        active = await self._reap_if_stale(active)
        if active is not None and active.status not in ("pending", "running"):
            active = None  # just got reaped — no longer "active"

        # Cooldown
        seconds_since = await self._seconds_since_last_run(user_id)
        cooldown_remaining = 0
        if seconds_since is not None:
            cooldown_remaining = max(
                0,
                settings.discovery_manual_cooldown_seconds - int(seconds_since),
            )

        # Quota reset_at
        earliest = await self._earliest_run_in_window(user_id)
        reset_at = (
            (earliest + timedelta(hours=24)).isoformat()
            if earliest
            else None
        )

        # Next automatic discovery — computed from the cron schedule on the
        # server so frontend doesn't have to know cron syntax.
        next_scheduled_at = _next_cron_fire(
            settings.discovery_schedule_cron, _now_utc()
        )

        return {
            "daily": {
                "used": used,
                "limit": limit,
                "remaining": max(0, limit - used),
                "reset_at": reset_at,
            },
            "cooldown_seconds_remaining": cooldown_remaining,
            "next_scheduled_at": next_scheduled_at.isoformat()
            if next_scheduled_at
            else None,
            "last_run": _serialize_run(last_completed),
            "active_run": _serialize_run(active),
        }

    async def trigger(
        self, user_id: uuid.UUID, trace_id: str = ""
    ) -> DiscoveryRun:
        """Validate, record, run the pipeline synchronously, and return the
        DiscoveryRun already in its terminal state (completed or failed)."""

        # Quota
        used = await self._count_runs_last_24h(user_id)
        limit = settings.discovery_manual_daily_limit
        if used >= limit:
            earliest = await self._earliest_run_in_window(user_id)
            reset_at = (
                (earliest + timedelta(hours=24))
                if earliest
                else _now_utc() + timedelta(hours=24)
            )
            raise QuotaExceededError(used=used, limit=limit, reset_at=reset_at)

        # Cooldown
        seconds_since = await self._seconds_since_last_run(user_id)
        if seconds_since is not None:
            cd = settings.discovery_manual_cooldown_seconds
            if seconds_since < cd:
                raise CooldownActiveError(seconds_remaining=int(cd - seconds_since))

        # Resolve queries from the user's latest search plan — auto-generate
        # one from the user's interests if they don't have one yet (so the
        # button works on the first click), or if they've added an interest
        # since the plan was generated (so it doesn't just search the same
        # stale topics forever — see _has_interests_added_since).
        existing_plan = await self._latest_search_plan(user_id)
        queries = self._plan_queries(existing_plan)
        stale = existing_plan is not None and await self._has_interests_added_since(
            user_id, existing_plan.created_at
        )
        if not queries or stale:
            from application.services.agents.research_planning_agent import (
                ResearchPlanningAgent,
            )
            from infrastructure.llm.providers import get_llm_provider

            agent = ResearchPlanningAgent(self._db, get_llm_provider("low"))
            new_plan = await agent.generate_search_plan(user_id, trace_id)
            queries = self._plan_queries(new_plan)
            if not queries:
                raise NoSearchPlanError(
                    "Couldn't find anything to search for — add a few "
                    "interests on your profile first."
                )

        run = DiscoveryRun(
            user_id=user_id,
            task_id=f"sync-{uuid.uuid4()}",
            status="running",
            trigger_type="personalized",
            search_queries={"queries": queries},
            started_at=_now_utc(),
        )
        self._db.add(run)
        await self._db.commit()  # visible immediately in case the run below fails hard

        logger.info(
            "discovery_run_started",
            run_id=str(run.id),
            user_id=str(user_id),
            query_count=len(queries),
            trace_id=trace_id,
        )

        # Run inline — see module docstring for why this isn't a Celery task.
        # Each phase uses its own fresh session (imported from run_pipeline)
        # rather than self._db, since that's a long-lived request-scoped
        # session and these phases can each touch hundreds of rows.
        from run_pipeline import run_discovery, run_processing_all, run_ranking_for_user

        try:
            new_count = await run_discovery(search_queries=queries, trace_id=trace_id)
            await run_processing_all(trace_id=trace_id, max_batches=5)
            rec_count = await run_ranking_for_user(user_id, trace_id=trace_id)
            run.status = "completed"
            run.new_items_count = new_count
            run.completed_at = _now_utc()
            await self._db.commit()
            logger.info(
                "discovery_run_completed",
                run_id=str(run.id),
                new_items=new_count,
                recommendations=rec_count,
                trace_id=trace_id,
            )
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = _now_utc()
            await self._db.commit()
            logger.error(
                "discovery_run_failed",
                run_id=str(run.id),
                error=str(exc),
                trace_id=trace_id,
            )

        return run

    async def get_run(
        self, user_id: uuid.UUID, run_id: uuid.UUID
    ) -> Optional[DiscoveryRun]:
        stmt = (
            select(DiscoveryRun)
            .where(DiscoveryRun.id == run_id)
            .where(DiscoveryRun.user_id == user_id)
        )
        result = await self._db.execute(stmt)
        run = result.scalar_one_or_none()
        return await self._reap_if_stale(run)


def _serialize_run(run: Optional[DiscoveryRun]) -> Optional[dict]:
    if run is None:
        return None
    return {
        "id": str(run.id),
        "task_id": run.task_id,
        "status": run.status,
        "trigger_type": run.trigger_type,
        "new_items_count": run.new_items_count,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def _next_cron_fire(cron_expr: str, after: datetime) -> Optional[datetime]:
    """Compute the next time a cron expression fires after `after`.

    Uses croniter if available (it ships transitively via celery), with a
    safe fallback that returns None so the UI just hides the field instead
    of crashing.
    """
    try:
        from croniter import croniter

        # croniter is timezone-naive-on-input by default but preserves tzinfo
        # if you pass an aware datetime.
        itr = croniter(cron_expr, after)
        return itr.get_next(datetime)
    except Exception as e:
        logger.warning("next_cron_fire_failed", error=str(e), cron=cron_expr)
        return None
