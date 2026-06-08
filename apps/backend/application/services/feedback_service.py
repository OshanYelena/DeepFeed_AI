"""
DeepFeed AI - Behavioral Signal Tracking (M11)
Tracks reading events, feedback events, and stores behavioral signals.
These signals feed the Agentic Adaptation Layer.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import (
    Feedback, UserInterestSignal, Recommendation, ContentItem,
)
from domain.events.events import FeedbackReceived
from logger import get_logger

logger = get_logger(__name__)

# Feedback type to signal strength mapping (TDS §13.6)
FEEDBACK_SIGNAL_MAP = {
    "like": 0.8,
    "bookmark": 0.9,
    "read": 0.4,
    "dislike": -0.7,
    "ignore": -0.3,
}


class FeedbackService:
    """Records user feedback and emits behavioral signals."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record_feedback(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        feedback_type: str,
        trace_id: str,
    ) -> Feedback:
        """
        Record user feedback and corresponding behavioral signal.
        All writes through application service — never direct DB manipulation.
        """
        if feedback_type not in FEEDBACK_SIGNAL_MAP:
            raise ValueError(f"Invalid feedback_type: {feedback_type}. Must be one of {list(FEEDBACK_SIGNAL_MAP.keys())}")

        # Verify recommendation belongs to user
        rec_result = await self._db.execute(
            select(Recommendation).where(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == user_id,
            )
        )
        rec = rec_result.scalar_one_or_none()
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found for user")

        signal_strength = FEEDBACK_SIGNAL_MAP[feedback_type]

        # Create feedback record
        feedback = Feedback(
            user_id=user_id,
            recommendation_id=recommendation_id,
            feedback_type=feedback_type,
            feedback_value=signal_strength,
        )
        self._db.add(feedback)

        # Create behavioral signal
        signal = UserInterestSignal(
            user_id=user_id,
            content_item_id=rec.content_item_id,
            signal_type=feedback_type,
            signal_strength=signal_strength,
        )
        self._db.add(signal)
        await self._db.flush()

        logger.info(
            "feedback_recorded",
            user_id=str(user_id),
            recommendation_id=str(recommendation_id),
            feedback_type=feedback_type,
            signal_strength=signal_strength,
            trace_id=trace_id,
        )
        return feedback

    async def record_read_event(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        duration_seconds: int,
        trace_id: str,
    ) -> None:
        """Record a read duration signal. Longer reads = stronger positive signal."""
        rec_result = await self._db.execute(
            select(Recommendation).where(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == user_id,
            )
        )
        rec = rec_result.scalar_one_or_none()
        if not rec:
            return

        # Signal strength based on reading duration
        if duration_seconds >= 300:
            strength = 0.7  # 5+ minutes = strong signal
        elif duration_seconds >= 60:
            strength = 0.4  # 1-5 minutes = moderate
        else:
            strength = 0.1  # < 1 minute = weak

        signal = UserInterestSignal(
            user_id=user_id,
            content_item_id=rec.content_item_id,
            signal_type="read",
            signal_strength=strength,
            duration_seconds=duration_seconds,
        )
        self._db.add(signal)
        await self._db.flush()

        logger.info(
            "read_signal_recorded",
            user_id=str(user_id),
            duration_seconds=duration_seconds,
            strength=strength,
            trace_id=trace_id,
        )
