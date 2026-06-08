"""
DeepFeed AI - Feed Service (M9) & Summarization Service (M10)
Feed: paginates and filters user recommendations.
Summarization: generates AI summaries with LLM fallback.
"""
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from infrastructure.database.models import (
    Recommendation, RecommendationTrace, ContentItem,
    Source, Summary, ProcessedContent,
)
from domain.interfaces.llm_provider import LLMProvider
from logger import get_logger

logger = get_logger(__name__)


# ── Feed Service ──────────────────────────────────────────────────────────────

class FeedService:
    """Generates and retrieves personalized feed (TDS §7.6)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_feed(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        min_score: Optional[float] = None,
        trace_id: str = "",
    ) -> List[dict]:
        stmt = (
            select(Recommendation)
            .options(
                selectinload(Recommendation.content_item).selectinload(ContentItem.source),
                selectinload(Recommendation.content_item).selectinload(ContentItem.summaries),
                selectinload(Recommendation.trace),
            )
            .where(Recommendation.user_id == user_id)
        )

        if min_score is not None:
            stmt = stmt.where(Recommendation.final_score >= min_score)

        if content_type:
            stmt = stmt.join(ContentItem).where(ContentItem.content_type == content_type)

        stmt = stmt.order_by(Recommendation.final_score.desc()).offset(offset).limit(limit)

        result = await self._db.execute(stmt)
        recommendations = list(result.scalars().all())

        feed_items = []
        for rec in recommendations:
            item = rec.content_item
            source = item.source if item else None
            summary = item.summaries if item else None
            trace = rec.trace

            feed_item = {
                "recommendation_id": str(rec.id),
                "title": item.title if item else "",
                "url": item.url if item else "",
                "source": source.name if source else "",
                "source_type": source.source_type if source else "",
                "content_type": item.content_type if item else "",
                "published_at": item.published_at.isoformat() if item and item.published_at else None,
                "final_score": rec.final_score,
                "relevance_score": rec.relevance_score,
                "credibility_score": rec.credibility_score,
                "freshness_score": rec.freshness_score,
                "rank_position": rec.rank_position,
                "summary_short": summary.summary_short if summary else None,
                "why_recommended": trace.explanation if trace else "Recommended based on your interests.",
                "matched_interests": trace.matched_interests.get("interests", []) if trace and trace.matched_interests else [],
            }
            feed_items.append(feed_item)

        logger.info("feed_generated", user_id=str(user_id), count=len(feed_items), trace_id=trace_id)
        return feed_items

    async def get_recommendation_detail(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        trace_id: str = "",
    ) -> Optional[dict]:
        result = await self._db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.content_item).selectinload(ContentItem.source),
                selectinload(Recommendation.content_item).selectinload(ContentItem.summaries),
                selectinload(Recommendation.content_item).selectinload(ContentItem.content_topics),
                selectinload(Recommendation.trace),
            )
            .where(
                and_(
                    Recommendation.id == recommendation_id,
                    Recommendation.user_id == user_id,
                )
            )
        )
        rec = result.scalar_one_or_none()
        if not rec:
            return None

        item = rec.content_item
        summary = item.summaries if item else None
        trace = rec.trace

        return {
            "recommendation_id": str(rec.id),
            "title": item.title if item else "",
            "url": item.url if item else "",
            "author": item.author if item else None,
            "content_type": item.content_type if item else "",
            "published_at": item.published_at.isoformat() if item and item.published_at else None,
            "final_score": rec.final_score,
            "scoring_breakdown": trace.scoring_breakdown if trace else {},
            "summary_short": summary.summary_short if summary else None,
            "summary_detailed": summary.summary_detailed if summary else None,
            "key_takeaways": summary.key_takeaways if summary else None,
            "why_recommended": trace.explanation if trace else "",
            "matched_interests": trace.matched_interests.get("interests", []) if trace and trace.matched_interests else [],
            "topics": [
                {"name": t.topic_name, "confidence": t.confidence}
                for t in (item.content_topics if item else [])
            ],
        }


# ── Summarization Service ─────────────────────────────────────────────────────

class SummarizationService:
    """
    Generates AI summaries for content items (TDS §14.2, §14.6).
    Falls back to keyword extraction if LLM unavailable.
    """

    def __init__(self, db: AsyncSession, llm_provider: Optional[LLMProvider] = None) -> None:
        self._db = db
        self._llm = llm_provider

    async def summarize_content_item(self, content_item_id: uuid.UUID, trace_id: str) -> bool:
        """Generate and store summary for a content item."""
        # Check if already summarized
        existing = await self._db.execute(
            select(Summary).where(Summary.content_item_id == content_item_id)
        )
        if existing.scalar_one_or_none():
            return True

        # Load processed content
        result = await self._db.execute(
            select(ProcessedContent)
            .options(selectinload(ProcessedContent.content_item))
            .where(ProcessedContent.content_item_id == content_item_id)
        )
        processed = result.scalar_one_or_none()
        if not processed:
            logger.warning("no_processed_content_for_summary", content_item_id=str(content_item_id))
            return False

        item = processed.content_item
        text = processed.clean_text or processed.abstract or ""

        if not text.strip():
            return False

        try:
            if self._llm:
                short, detailed, takeaways = await self._generate_with_llm(item.title, text)
                generated_by = "model"
            else:
                short, detailed, takeaways = self._generate_fallback(item.title, text)
                generated_by = "fallback"

            summary = Summary(
                content_item_id=content_item_id,
                summary_short=short,
                summary_detailed=detailed,
                key_takeaways=takeaways,
                generated_by=generated_by,
            )
            self._db.add(summary)

            # Update item status
            item.status = "summarized"
            await self._db.flush()

            logger.info("summary_generated", content_item_id=str(content_item_id), by=generated_by, trace_id=trace_id)
            return True

        except Exception as e:
            logger.error("summarization_failed", content_item_id=str(content_item_id), error=str(e), trace_id=trace_id)
            return False

    async def _generate_with_llm(self, title: str, text: str) -> tuple[str, str, dict]:
        """Generate summaries using LLM."""
        prompt = f"""Summarize this technical content.

Title: {title}

Content: {text[:4000]}

Respond in JSON format:
{{
  "short": "2-3 sentence summary",
  "detailed": "5-7 sentence detailed summary",
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"]
}}"""
        response = await self._llm.generate(prompt, max_tokens=600)

        import json, re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return (
                data.get("short", ""),
                data.get("detailed", ""),
                {"takeaways": data.get("key_takeaways", [])},
            )
        return response.content[:300], response.content[:600], {}

    def _generate_fallback(self, title: str, text: str) -> tuple[str, str, dict]:
        """Simple fallback: first sentences as summary."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 30]
        short = ". ".join(sentences[:2]) + "." if sentences else title
        detailed = ". ".join(sentences[:5]) + "." if sentences else title
        # Extract keywords as takeaways
        words = set(text.lower().split())
        tech_keywords = [w for w in words if len(w) > 6 and w.isalpha()][:5]
        return short, detailed, {"takeaways": tech_keywords, "source": "fallback"}
