"""
DeepFeed AI - Ranking Engine (M8)
Implements the V1 scoring formula from TDS §12.4:
  Final Score = Relevance×0.40 + Credibility×0.20 + Freshness×0.15 + Novelty×0.15 + Feedback×0.10
Generates Recommendations with RecommendationTraces for explainability.
"""
import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from infrastructure.database.models import (
    ContentItem, ContentTopic, Interest, Source,
    Recommendation, RecommendationTrace, Feedback,
    UserTopicPreference, SourcePreference, ProcessedContent,
)
from logger import get_logger

logger = get_logger(__name__)

# ── Ranking Weights (TDS §12.4) ───────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "relevance": 0.40,
    "credibility": 0.20,
    "freshness": 0.15,
    "novelty": 0.15,
    "feedback": 0.10,
}


@dataclass
class ScoringResult:
    relevance_score: float
    credibility_score: float
    freshness_score: float
    novelty_score: float
    feedback_score: float
    final_score: float
    matched_interests: List[str]
    explanation: str


class RankingEngine:
    """
    Core ranking engine. Scores content items against a user profile
    and generates recommendations with full traceability.
    """

    def __init__(self, db: AsyncSession, weights: Optional[dict] = None) -> None:
        self._db = db
        self._weights = weights or DEFAULT_WEIGHTS

    async def generate_recommendations(
        self,
        user_id: uuid.UUID,
        content_item_ids: Optional[List[uuid.UUID]] = None,
        limit: int = 50,
        trace_id: str = "",
    ) -> List[Recommendation]:
        """
        Score and rank content items for a user.
        Creates Recommendation + RecommendationTrace records.
        """
        logger.info("ranking_start", user_id=str(user_id), trace_id=trace_id)

        # Load user context
        interests = await self._load_interests(user_id)
        topic_prefs = await self._load_topic_preferences(user_id)
        source_prefs = await self._load_source_preferences(user_id)
        recent_feedback = await self._load_recent_feedback(user_id)

        # Load processable content items
        items = await self._load_content_items(content_item_ids, limit * 3)
        if not items:
            logger.info("no_content_to_rank", user_id=str(user_id), trace_id=trace_id)
            return []

        # Score each item
        scored: List[Tuple[ContentItem, ScoringResult]] = []
        for item in items:
            try:
                score = await self._score_item(item, interests, topic_prefs, source_prefs, recent_feedback)
                scored.append((item, score))
            except Exception as e:
                logger.warning("item_scoring_failed", item_id=str(item.id), error=str(e), trace_id=trace_id)

        # Sort by final_score descending
        scored.sort(key=lambda x: x[1].final_score, reverse=True)
        top = scored[:limit]

        # Persist recommendations
        recommendations = []
        for rank, (item, score) in enumerate(top, start=1):
            rec = Recommendation(
                user_id=user_id,
                content_item_id=item.id,
                relevance_score=score.relevance_score,
                freshness_score=score.freshness_score,
                credibility_score=score.credibility_score,
                novelty_score=score.novelty_score,
                final_score=score.final_score,
                rank_position=rank,
            )
            self._db.add(rec)
            await self._db.flush()

            trace = RecommendationTrace(
                recommendation_id=rec.id,
                matched_interests={"interests": score.matched_interests},
                scoring_breakdown={
                    "relevance": score.relevance_score,
                    "credibility": score.credibility_score,
                    "freshness": score.freshness_score,
                    "novelty": score.novelty_score,
                    "feedback": score.feedback_score,
                    "weights": self._weights,
                },
                explanation=score.explanation,
            )
            self._db.add(trace)
            recommendations.append(rec)

        logger.info("ranking_complete", user_id=str(user_id), count=len(recommendations), trace_id=trace_id)
        return recommendations

    async def _score_item(
        self,
        item: ContentItem,
        interests: List[Interest],
        topic_prefs: List[UserTopicPreference],
        source_prefs: List[SourcePreference],
        recent_feedback: dict,
    ) -> ScoringResult:

        # Load item topics
        topics_result = await self._db.execute(
            select(ContentTopic).where(ContentTopic.content_item_id == item.id)
        )
        item_topics = {t.topic_name.lower(): t.confidence for t in topics_result.scalars().all()}

        # Load source
        source_result = await self._db.execute(select(Source).where(Source.id == item.source_id))
        source = source_result.scalar_one_or_none()
        source_trust = source.trust_score if source else 0.5

        # ── 1. Relevance Score ────────────────────────────────────────────────
        relevance = 0.0
        matched_interests = []

        # Match explicit interests
        for interest in interests:
            interest_lower = interest.name.lower()
            for topic_name, topic_conf in item_topics.items():
                if interest_lower in topic_name or topic_name in interest_lower:
                    relevance += interest.weight * topic_conf
                    if interest.name not in matched_interests:
                        matched_interests.append(interest.name)

        # Boost from learned topic preferences
        for pref in topic_prefs:
            pref_lower = pref.topic.lower()
            for topic_name, topic_conf in item_topics.items():
                if pref_lower in topic_name or topic_name in pref_lower:
                    relevance += pref.weight * pref.confidence * topic_conf * 0.5

        relevance = min(relevance, 1.0)

        # ── 2. Credibility Score ──────────────────────────────────────────────
        # Source trust + personal source preference adjustments
        source_id = item.source_id
        personal_trust = next(
            (sp.personal_trust_score for sp in source_prefs if sp.source_id == source_id),
            source_trust,
        )
        credibility = (source_trust * 0.6 + personal_trust * 0.4)

        # ── 3. Freshness Score ────────────────────────────────────────────────
        freshness = self._compute_freshness(item.published_at or item.discovered_at)

        # ── 4. Novelty Score ──────────────────────────────────────────────────
        # Penalize if user has seen similar items (simplified: use feedback history)
        novelty = 1.0
        if str(item.id) in recent_feedback:
            novelty = 0.2  # Already interacted

        # ── 5. Feedback Score ─────────────────────────────────────────────────
        feedback_score = 0.5  # Neutral default

        # ── Final Weighted Score ──────────────────────────────────────────────
        w = self._weights
        final = (
            relevance * w["relevance"]
            + credibility * w["credibility"]
            + freshness * w["freshness"]
            + novelty * w["novelty"]
            + feedback_score * w["feedback"]
        )

        # Build explanation
        if matched_interests:
            explanation = f"Strong match with your interests: {', '.join(matched_interests[:3])}."
        elif relevance > 0:
            explanation = "Matches topics in your learning profile."
        else:
            explanation = "Recommended based on source credibility and freshness."

        if credibility > 0.85:
            explanation += " From a highly trusted source."

        return ScoringResult(
            relevance_score=round(relevance, 4),
            credibility_score=round(credibility, 4),
            freshness_score=round(freshness, 4),
            novelty_score=round(novelty, 4),
            feedback_score=round(feedback_score, 4),
            final_score=round(final, 4),
            matched_interests=matched_interests,
            explanation=explanation,
        )

    def _compute_freshness(self, published_at: Optional[datetime]) -> float:
        """Exponential decay: score = e^(-0.1 * days_old). Max 1.0."""
        if not published_at:
            return 0.3
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        days_old = max(0, (now - published_at).total_seconds() / 86400)
        return round(math.exp(-0.1 * days_old), 4)

    async def _load_interests(self, user_id: uuid.UUID) -> List[Interest]:
        result = await self._db.execute(select(Interest).where(Interest.user_id == user_id))
        return list(result.scalars().all())

    async def _load_topic_preferences(self, user_id: uuid.UUID) -> List[UserTopicPreference]:
        result = await self._db.execute(
            select(UserTopicPreference).where(UserTopicPreference.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _load_source_preferences(self, user_id: uuid.UUID) -> List[SourcePreference]:
        result = await self._db.execute(
            select(SourcePreference).where(SourcePreference.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _load_recent_feedback(self, user_id: uuid.UUID) -> dict:
        result = await self._db.execute(
            select(Feedback).where(Feedback.user_id == user_id)
        )
        return {str(f.recommendation_id): f.feedback_type for f in result.scalars().all()}

    async def _load_content_items(
        self,
        item_ids: Optional[List[uuid.UUID]],
        limit: int,
    ) -> List[ContentItem]:
        stmt = select(ContentItem).where(ContentItem.status == "processed")
        if item_ids:
            stmt = stmt.where(ContentItem.id.in_(item_ids))
        stmt = stmt.order_by(ContentItem.discovered_at.desc()).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
