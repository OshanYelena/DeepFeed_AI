"""
DeepFeed AI - Celery Task Definitions
All background jobs: Discovery, Processing, Ranking, Summarization, Adaptation, Reflection.
Each job follows the lifecycle: Pending → Running → Completed|Failed → Retry
Idempotent by design (TDS §9.7).
"""
import asyncio
import uuid
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from workers.celery_app import celery_app
from logger import get_logger

logger = get_logger(__name__)


def _run_async(coro):
    """Run async code from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_db_session():
    """Get a database session for use in workers."""
    from infrastructure.database.connection import AsyncSessionLocal
    return AsyncSessionLocal()


# ── Discovery Task ────────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_discovery_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_discovery_task(self, source_id: str = None, trace_id: str = None):
    """Run content discovery for all or a specific source."""
    trace_id = trace_id or str(uuid.uuid4())
    logger.info("discovery_task_start", task_id=self.request.id, trace_id=trace_id)

    async def _run():
        from application.services.discovery_service import DiscoveryService
        async with await _get_db_session() as db:
            service = DiscoveryService(db)
            src_uuid = uuid.UUID(source_id) if source_id else None
            new_count = await service.run_discovery(source_id=src_uuid, trace_id=trace_id)
            await db.commit()
            return new_count

    try:
        new_count = _run_async(_run())
        logger.info("discovery_task_complete", new_items=new_count, trace_id=trace_id)
        return {"status": "completed", "new_items": new_count}
    except Exception as exc:
        logger.error("discovery_task_failed", error=str(exc), trace_id=trace_id)
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}


# ── Personalized Discovery Task ───────────────────────────────────────────────
# Triggered by the "Discover Now" button. Reads the user's latest SearchPlan
# queries (passed in by the API layer) and feeds them to DiscoveryService so
# providers like RSS/arXiv that accept query input return user-relevant
# candidates instead of their default firehose.
#
# This task also updates the DiscoveryRun row so the UI can observe progress.

@celery_app.task(
    name="workers.tasks.run_personalized_discovery_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_personalized_discovery_task(
    self,
    user_id: str,
    search_queries: list = None,
    trace_id: str = None,
):
    """Manual, personalized discovery triggered by an authenticated user."""
    from datetime import datetime, timezone
    from sqlalchemy import select

    trace_id = trace_id or str(uuid.uuid4())
    task_id = self.request.id
    user_uuid = uuid.UUID(user_id)
    queries = list(search_queries or [])

    logger.info(
        "personalized_discovery_start",
        task_id=task_id,
        user_id=user_id,
        query_count=len(queries),
        trace_id=trace_id,
    )

    async def _mark_running():
        # Flip status from 'pending' → 'running' so the UI can show the
        # right phase. Best-effort: if the row isn't there yet (race with
        # the API commit) we'll just no-op.
        from infrastructure.database.models import DiscoveryRun
        async with await _get_db_session() as db:
            row = (await db.execute(
                select(DiscoveryRun).where(DiscoveryRun.task_id == task_id)
            )).scalar_one_or_none()
            if row is not None:
                row.status = "running"
                await db.commit()

    async def _run_discovery():
        from application.services.discovery_service import DiscoveryService
        async with await _get_db_session() as db:
            service = DiscoveryService(db)
            new_count = await service.run_discovery(
                search_queries=queries or None,
                trace_id=trace_id,
            )
            await db.commit()
            return new_count

    async def _run_processing():
        # Discovery only creates ContentItem rows with status='discovered' —
        # they're not visible in anyone's feed until extracted + classified.
        # Loop batches here so a single "Discover Now" click can actually
        # finish the pipeline instead of waiting on the 30-minute beat cycle.
        from application.services.content_service import ContentProcessingService
        from infrastructure.llm.providers import get_llm_provider
        llm = get_llm_provider("low")
        total = 0
        for _ in range(15):  # cap: 15 * batch_size(20) = 300 items per run
            async with await _get_db_session() as db:
                service = ContentProcessingService(db, llm)
                count = await service.process_pending(batch_size=20, trace_id=trace_id)
                await db.commit()
            total += count
            if count == 0:
                break
        return total

    async def _run_ranking():
        from application.services.ranking_service import RankingEngine
        async with await _get_db_session() as db:
            engine = RankingEngine(db)
            recs = await engine.generate_recommendations(user_uuid, trace_id=trace_id)
            await db.commit()
            return len(recs)

    async def _mark_terminal(status: str, new_count: int = None, error: str = None):
        from infrastructure.database.models import DiscoveryRun
        async with await _get_db_session() as db:
            row = (await db.execute(
                select(DiscoveryRun).where(DiscoveryRun.task_id == task_id)
            )).scalar_one_or_none()
            if row is not None:
                row.status = status
                row.new_items_count = new_count
                row.error_message = error
                row.completed_at = datetime.now(timezone.utc)
                await db.commit()

    try:
        _run_async(_mark_running())
        new_count = _run_async(_run_discovery())
        processed_count = _run_async(_run_processing())
        rec_count = _run_async(_run_ranking())
        _run_async(_mark_terminal("completed", new_count=new_count))
        logger.info(
            "personalized_discovery_complete",
            task_id=task_id,
            user_id=user_id,
            new_items=new_count,
            processed_items=processed_count,
            recommendations=rec_count,
            trace_id=trace_id,
        )
        return {
            "status": "completed",
            "new_items": new_count,
            "processed_items": processed_count,
            "recommendations": rec_count,
        }
    except Exception as exc:
        logger.error(
            "personalized_discovery_failed",
            task_id=task_id,
            user_id=user_id,
            error=str(exc),
            trace_id=trace_id,
        )
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            # Final failure — record it on the run row before returning.
            _run_async(_mark_terminal("failed", error=str(exc)))
            return {"status": "failed", "error": str(exc)}


# ── Content Processing Task ───────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_processing_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_processing_task(self, content_item_id: str = None, trace_id: str = None):
    """Process a specific content item or batch of pending items."""
    trace_id = trace_id or str(uuid.uuid4())
    logger.info("processing_task_start", task_id=self.request.id, trace_id=trace_id)

    async def _run():
        from application.services.content_service import ContentProcessingService
        from infrastructure.llm.providers import get_llm_provider
        async with await _get_db_session() as db:
            llm = get_llm_provider("low")
            service = ContentProcessingService(db, llm)
            if content_item_id:
                ok = await service.process_content_item(uuid.UUID(content_item_id), trace_id)
                count = 1 if ok else 0
            else:
                count = await service.process_pending(batch_size=20, trace_id=trace_id)
            await db.commit()
            return count

    try:
        count = _run_async(_run())
        logger.info("processing_task_complete", processed=count, trace_id=trace_id)
        return {"status": "completed", "processed": count}
    except Exception as exc:
        logger.error("processing_task_failed", error=str(exc), trace_id=trace_id)
        try:
            raise self.retry(exc=exc, countdown=120 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}


# ── Ranking Task ──────────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_ranking_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_ranking_task(self, user_id: str, trace_id: str = None):
    """Generate recommendations for a specific user."""
    trace_id = trace_id or str(uuid.uuid4())
    logger.info("ranking_task_start", user_id=user_id, task_id=self.request.id, trace_id=trace_id)

    async def _run():
        from application.services.ranking_service import RankingEngine
        async with await _get_db_session() as db:
            engine = RankingEngine(db)
            recs = await engine.generate_recommendations(uuid.UUID(user_id), trace_id=trace_id)
            await db.commit()
            return len(recs)

    try:
        count = _run_async(_run())
        logger.info("ranking_task_complete", user_id=user_id, recommendations=count, trace_id=trace_id)
        return {"status": "completed", "recommendations": count}
    except Exception as exc:
        logger.error("ranking_task_failed", user_id=user_id, error=str(exc), trace_id=trace_id)
        try:
            raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}


# ── Summarization Task ────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_summarization_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def run_summarization_task(self, content_item_id: str, trace_id: str = None):
    """Generate summary for a content item."""
    trace_id = trace_id or str(uuid.uuid4())

    async def _run():
        from application.services.feed_service import SummarizationService
        from infrastructure.llm.providers import get_llm_provider
        async with await _get_db_session() as db:
            llm = get_llm_provider("medium")
            service = SummarizationService(db, llm)
            ok = await service.summarize_content_item(uuid.UUID(content_item_id), trace_id)
            await db.commit()
            return ok

    try:
        ok = _run_async(_run())
        return {"status": "completed" if ok else "skipped"}
    except Exception as exc:
        logger.error("summarization_task_failed", content_item_id=content_item_id, error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}


# ── Adaptation Task ───────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_adaptation_task",
    bind=True,
    max_retries=2,
)
def run_adaptation_task(self, user_id: str = None, trace_id: str = None):
    """Run adaptation cycle for a user or all users."""
    trace_id = trace_id or str(uuid.uuid4())
    logger.info("adaptation_task_start", user_id=user_id, trace_id=trace_id)

    async def _run():
        from application.services.agents.adaptation_engine import AdaptationEngine
        from infrastructure.llm.providers import get_llm_provider
        from infrastructure.database.models import User
        from sqlalchemy import select

        async with await _get_db_session() as db:
            llm = get_llm_provider("medium")
            engine = AdaptationEngine(db, llm)

            if user_id:
                user_ids = [uuid.UUID(user_id)]
            else:
                result = await db.execute(select(User.id))
                user_ids = [row[0] for row in result.all()]

            summaries = []
            for uid in user_ids:
                try:
                    summary = await engine.run_full_cycle(uid, trace_id)
                    summaries.append({"user_id": str(uid), "summary": summary})
                except Exception as e:
                    logger.error("user_adaptation_failed", user_id=str(uid), error=str(e))
            await db.commit()
            return summaries

    try:
        summaries = _run_async(_run())
        logger.info("adaptation_task_complete", count=len(summaries), trace_id=trace_id)
        return {"status": "completed", "users_processed": len(summaries)}
    except Exception as exc:
        logger.error("adaptation_task_failed", error=str(exc), trace_id=trace_id)
        raise self.retry(exc=exc, countdown=300)


# ── Reflection Task ───────────────────────────────────────────────────────────

@celery_app.task(
    name="workers.tasks.run_reflection_task",
    bind=True,
    max_retries=2,
)
def run_reflection_task(self, user_id: str = None, period: str = "daily", trace_id: str = None):
    """Run reflection for a user or all users."""
    trace_id = trace_id or str(uuid.uuid4())

    async def _run():
        from application.services.agents.adaptation_engine import ReflectionAgent
        from infrastructure.llm.providers import get_llm_provider
        from infrastructure.database.models import User
        from sqlalchemy import select

        async with await _get_db_session() as db:
            llm = get_llm_provider("large")
            agent = ReflectionAgent(db, llm)

            if user_id:
                user_ids = [uuid.UUID(user_id)]
            else:
                result = await db.execute(select(User.id))
                user_ids = [row[0] for row in result.all()]

            count = 0
            for uid in user_ids:
                try:
                    await agent.run(uid, period, trace_id)
                    count += 1
                except Exception as e:
                    logger.error("user_reflection_failed", user_id=str(uid), error=str(e))
            await db.commit()
            return count

    try:
        count = _run_async(_run())
        logger.info("reflection_task_complete", users=count, trace_id=trace_id)
        return {"status": "completed", "users_processed": count}
    except Exception as exc:
        logger.error("reflection_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)
