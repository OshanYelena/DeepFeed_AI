"""
DeepFeed AI - Manual pipeline runner

Runs Discovery -> Processing -> Ranking end-to-end, synchronously, by calling
the application services directly (no Celery/worker involved). Useful for
populating a feed on demand until the frontend has a real "Discover Now"
button wired all the way through, and for debugging the pipeline without
digging through worker logs.

Usage (run from inside the backend container):
    python run_pipeline.py                      # discovery + processing only
    python run_pipeline.py you@example.com       # + rank for that user
    python run_pipeline.py <user-uuid>           # + rank for that user
    python run_pipeline.py --all-users           # + rank for every user

From the host:
    docker exec deepfeed_backend python run_pipeline.py you@example.com
"""
import asyncio
import sys
import uuid
from typing import List, Optional

from sqlalchemy import select

from infrastructure.database.connection import AsyncSessionLocal
from infrastructure.database.models import User
from infrastructure.llm.providers import get_llm_provider
from application.services.discovery_service import DiscoveryService
from application.services.content_service import ContentProcessingService
from application.services.ranking_service import RankingEngine

TRACE_ID = "manual-pipeline-script"
MAX_PROCESSING_BATCHES = 30  # safety cap: 30 * batch_size(20) = 600 items/run


async def run_discovery() -> int:
    async with AsyncSessionLocal() as db:
        service = DiscoveryService(db)
        new_count = await service.run_discovery(trace_id=TRACE_ID)
        await db.commit()
    print(f"[discovery] {new_count} new content items")
    return new_count


async def run_processing_all() -> int:
    llm = get_llm_provider("low")
    total = 0
    for _ in range(MAX_PROCESSING_BATCHES):
        async with AsyncSessionLocal() as db:
            service = ContentProcessingService(db, llm)
            count = await service.process_pending(batch_size=20, trace_id=TRACE_ID)
            await db.commit()
        total += count
        print(f"[processing] batch processed {count} items (running total: {total})")
        if count == 0:
            break
    else:
        print(f"[processing] stopped after {MAX_PROCESSING_BATCHES} batches — "
              f"there may still be unprocessed items, run again to continue")
    return total


async def run_ranking_for_user(user_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as db:
        engine = RankingEngine(db)
        recs = await engine.generate_recommendations(user_id, trace_id=TRACE_ID)
        await db.commit()
    print(f"[ranking] {len(recs)} recommendations generated for user {user_id}")
    return len(recs)


async def resolve_user_ids(identifier: Optional[str]) -> List[uuid.UUID]:
    async with AsyncSessionLocal() as db:
        if identifier in (None, "--all-users"):
            result = await db.execute(select(User.id))
            return [row[0] for row in result.all()]
        try:
            return [uuid.UUID(identifier)]
        except ValueError:
            result = await db.execute(select(User.id).where(User.email == identifier))
            row = result.first()
            if not row:
                raise SystemExit(f"No user found with email {identifier!r}")
            return [row[0]]


async def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    await run_discovery()
    await run_processing_all()

    if arg is None:
        print("[ranking] skipped — pass an email, a user id, or --all-users to rank")
        return

    for user_id in await resolve_user_ids(arg):
        await run_ranking_for_user(user_id)


if __name__ == "__main__":
    asyncio.run(main())
