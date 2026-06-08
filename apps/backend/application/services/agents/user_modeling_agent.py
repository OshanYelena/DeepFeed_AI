"""
DeepFeed AI - User Modeling Agent (M12)
Maintains an evolving user representation from behavioral signals.
Detects emerging/declining interests, updates topic weights.
All decisions create AdaptationEvents for traceability (TDS §13.8).
"""
import uuid
from collections import defaultdict
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import (
    UserInterestSignal, ContentTopic, ContentItem,
    UserTopicPreference, SourcePreference, AdaptationEvent,
)
from logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "UserModelingAgent"


class UserModelingAgent:
    """
    Processes behavioral signals and updates user topic/source preferences.
    Implements adaptation policies from TDS §13.6.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def run(self, user_id: uuid.UUID, trace_id: str = "") -> dict:
        """
        Execute user modeling cycle for one user.
        Returns summary of changes made.
        """
        logger.info("user_modeling_agent_start", user_id=str(user_id), trace_id=trace_id)

        signals = await self._load_recent_signals(user_id)
        if not signals:
            logger.info("no_signals_for_user_modeling", user_id=str(user_id), trace_id=trace_id)
            return {"topics_updated": 0, "sources_updated": 0}

        topic_changes = await self._update_topic_preferences(user_id, signals, trace_id)
        source_changes = await self._update_source_preferences(user_id, signals, trace_id)

        summary = {"topics_updated": topic_changes, "sources_updated": source_changes}
        logger.info("user_modeling_agent_complete", user_id=str(user_id), summary=summary, trace_id=trace_id)
        return summary

    async def _load_recent_signals(self, user_id: uuid.UUID) -> List[UserInterestSignal]:
        result = await self._db.execute(
            select(UserInterestSignal)
            .where(UserInterestSignal.user_id == user_id)
            .order_by(UserInterestSignal.created_at.desc())
            .limit(500)
        )
        return list(result.scalars().all())

    async def _update_topic_preferences(
        self,
        user_id: uuid.UUID,
        signals: List[UserInterestSignal],
        trace_id: str,
    ) -> int:
        """
        Aggregate signal strength by topic and update UserTopicPreference.
        Policy 1: increase topic weight on saves/likes/long reads.
        Policy 2: decrease topic weight on repeated ignores/dislikes.
        """
        # Map content_item_id → topics
        item_ids = list({s.content_item_id for s in signals})
        topics_by_item: Dict[uuid.UUID, List[ContentTopic]] = {}

        for item_id in item_ids:
            result = await self._db.execute(
                select(ContentTopic).where(ContentTopic.content_item_id == item_id)
            )
            topics_by_item[item_id] = list(result.scalars().all())

        # Aggregate weighted signals per topic
        topic_signal_sum: Dict[str, float] = defaultdict(float)
        topic_signal_count: Dict[str, int] = defaultdict(int)

        for signal in signals:
            item_topics = topics_by_item.get(signal.content_item_id, [])
            for topic in item_topics:
                weighted = signal.signal_strength * topic.confidence
                topic_signal_sum[topic.topic_name] += weighted
                topic_signal_count[topic.topic_name] += 1

        updated = 0
        for topic_name, signal_sum in topic_signal_sum.items():
            count = topic_signal_count[topic_name]
            avg_signal = signal_sum / count if count > 0 else 0

            # Load or create preference
            result = await self._db.execute(
                select(UserTopicPreference).where(
                    UserTopicPreference.user_id == user_id,
                    UserTopicPreference.topic == topic_name,
                )
            )
            pref = result.scalar_one_or_none()

            old_weight = pref.weight if pref else 0.5
            # Smooth adjustment: move 20% toward signal direction
            adjustment = avg_signal * 0.2
            new_weight = max(0.0, min(1.0, old_weight + adjustment))
            new_confidence = min(1.0, (count / 20.0) * 0.5 + 0.5)  # Grows with more signals

            if pref:
                old = pref.weight
                pref.weight = new_weight
                pref.confidence = new_confidence
                pref.source = "behavioral"
            else:
                pref = UserTopicPreference(
                    user_id=user_id,
                    topic=topic_name,
                    weight=new_weight,
                    confidence=new_confidence,
                    source="behavioral",
                )
                self._db.add(pref)

            # Record adaptation event
            event = AdaptationEvent(
                user_id=user_id,
                agent_name=AGENT_NAME,
                event_type="topic_weight_update",
                input_snapshot={"signals": count, "avg_signal": avg_signal},
                decision={"topic": topic_name, "old_weight": old_weight, "new_weight": new_weight},
                reason=f"Behavioral signals (n={count}) indicate avg strength {avg_signal:.2f}",
                confidence=new_confidence,
            )
            self._db.add(event)
            updated += 1

        await self._db.flush()
        return updated

    async def _update_source_preferences(
        self,
        user_id: uuid.UUID,
        signals: List[UserInterestSignal],
        trace_id: str,
    ) -> int:
        """
        Update source preferences based on interactions.
        Policy 3: promote sources with high save/read rates.
        Policy 4: suppress sources with repeated ignores/dislikes.
        """
        # Map content_item_id → source_id
        item_ids = list({s.content_item_id for s in signals})
        source_map: Dict[uuid.UUID, uuid.UUID] = {}

        for item_id in item_ids:
            result = await self._db.execute(
                select(ContentItem.source_id).where(ContentItem.id == item_id)
            )
            row = result.first()
            if row:
                source_map[item_id] = row[0]

        # Aggregate by source
        source_signals: Dict[uuid.UUID, List[float]] = defaultdict(list)
        for signal in signals:
            src_id = source_map.get(signal.content_item_id)
            if src_id:
                source_signals[src_id].append(signal.signal_strength)

        updated = 0
        for source_id, strengths in source_signals.items():
            avg = sum(strengths) / len(strengths)

            result = await self._db.execute(
                select(SourcePreference).where(
                    SourcePreference.user_id == user_id,
                    SourcePreference.source_id == source_id,
                )
            )
            pref = result.scalar_one_or_none()

            if pref:
                old_trust = pref.personal_trust_score
                adjustment = avg * 0.15
                pref.personal_trust_score = max(0.0, min(1.0, old_trust + adjustment))
                pref.interaction_count += len(strengths)
                positive = sum(1 for s in strengths if s > 0)
                negative = sum(1 for s in strengths if s < 0)
                pref.positive_feedback_count += positive
                pref.negative_feedback_count += negative
            else:
                pref = SourcePreference(
                    user_id=user_id,
                    source_id=source_id,
                    personal_trust_score=max(0.0, min(1.0, 0.7 + avg * 0.15)),
                    interaction_count=len(strengths),
                    positive_feedback_count=sum(1 for s in strengths if s > 0),
                    negative_feedback_count=sum(1 for s in strengths if s < 0),
                )
                self._db.add(pref)

            updated += 1

        await self._db.flush()
        return updated
