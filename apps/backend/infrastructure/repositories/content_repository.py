"""
DeepFeed AI - Optimized Query Layer (M18 Performance Optimization)
Efficient batch queries and N+1 prevention for the ranking and feed pipelines.
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from infrastructure.database.models import (
    ContentItem, ContentTopic, Recommendation, Source,
)
from logger import get_logger

logger = get_logger(__name__)


class OptimizedContentLoader:
    """
    Batch-loads content with related data to avoid N+1 queries.
    Uses eager loading and pagination for performance.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def load_processable_batch(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContentItem]:
        """Load processed content items with topics eagerly loaded."""
        result = await self._db.execute(
            select(ContentItem)
            .options(
                selectinload(ContentItem.content_topics),
                selectinload(ContentItem.source),
            )
            .where(ContentItem.status == "processed")
            .order_by(ContentItem.discovered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def load_topics_for_items(
        self,
        item_ids: List[uuid.UUID],
    ) -> dict[uuid.UUID, List[ContentTopic]]:
        """Batch-load topics for a list of content items."""
        if not item_ids:
            return {}

        result = await self._db.execute(
            select(ContentTopic).where(ContentTopic.content_item_id.in_(item_ids))
        )
        topics = result.scalars().all()

        topics_by_item: dict[uuid.UUID, List[ContentTopic]] = {}
        for topic in topics:
            if topic.content_item_id not in topics_by_item:
                topics_by_item[topic.content_item_id] = []
            topics_by_item[topic.content_item_id].append(topic)

        return topics_by_item

    async def get_content_stats(self) -> dict:
        """Get aggregate content statistics for monitoring."""
        result = await self._db.execute(
            text("""
                SELECT
                    status,
                    COUNT(*) as count,
                    MIN(discovered_at) as oldest,
                    MAX(discovered_at) as newest
                FROM content_items
                GROUP BY status
                ORDER BY count DESC
            """)
        )
        rows = result.all()
        return {
            row.status: {
                "count": row.count,
                "oldest": row.oldest.isoformat() if row.oldest else None,
                "newest": row.newest.isoformat() if row.newest else None,
            }
            for row in rows
        }

    async def get_user_recommendation_stats(self, user_id: uuid.UUID) -> dict:
        """Get recommendation statistics for a user."""
        result = await self._db.execute(
            text("""
                SELECT
                    COUNT(*) as total,
                    AVG(final_score) as avg_score,
                    MAX(final_score) as max_score,
                    MIN(final_score) as min_score,
                    MAX(generated_at) as last_generated
                FROM recommendations
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)},
        )
        row = result.first()
        if not row or not row.total:
            return {"total": 0}

        return {
            "total": row.total,
            "avg_score": round(float(row.avg_score or 0), 3),
            "max_score": round(float(row.max_score or 0), 3),
            "min_score": round(float(row.min_score or 0), 3),
            "last_generated": row.last_generated.isoformat() if row.last_generated else None,
        }
