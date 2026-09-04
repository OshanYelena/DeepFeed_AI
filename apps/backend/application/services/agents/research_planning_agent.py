"""
DeepFeed AI - Research Planning Agent (M13)
Generates personalized search strategies (SearchPlans) based on user profile.
Uses LLM for query expansion when available.
All decisions recorded as AdaptationEvents.
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import (
    Interest, UserTopicPreference, SearchPlan, AdaptationEvent, UserProfile,
)
from domain.interfaces.llm_provider import LLMProvider
from logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "ResearchPlanningAgent"


class ResearchPlanningAgent:
    """
    Generates personalized search plans combining explicit interests
    and learned topic preferences. LLM is used for query expansion.
    """

    def __init__(self, db: AsyncSession, llm_provider: Optional[LLMProvider] = None) -> None:
        self._db = db
        self._llm = llm_provider

    async def generate_search_plan(
        self,
        user_id: uuid.UUID,
        trace_id: str = "",
    ) -> SearchPlan:
        """
        Generate a SearchPlan for the user.
        Returns the created SearchPlan.
        """
        logger.info("research_planning_agent_start", user_id=str(user_id), trace_id=trace_id)

        # Load user context
        interests = await self._load_interests(user_id)
        topic_prefs = await self._load_top_topic_preferences(user_id)
        profile = await self._load_profile(user_id)

        # Build base queries from interests
        base_queries = [i.name for i in interests]
        # Add top learned topics
        learned_topics = [p.topic for p in topic_prefs if p.weight > 0.6]
        all_topics = list(dict.fromkeys(base_queries + learned_topics))  # Deduplicate

        # Expand with LLM if available
        queries = await self._expand_queries(all_topics, profile)

        # Build source priorities
        source_priorities = self._build_source_priorities(profile)

        # Determine search depth
        depth = "deep" if (profile and profile.preferred_depth == "deep") else "normal"

        plan = SearchPlan(
            user_id=user_id,
            generated_by=AGENT_NAME,
            queries={"queries": queries},
            source_priorities={"sources": source_priorities},
            search_depth=depth,
            status="pending",
        )
        self._db.add(plan)
        await self._db.flush()

        # Record adaptation event
        event = AdaptationEvent(
            user_id=user_id,
            agent_name=AGENT_NAME,
            event_type="search_plan_generated",
            input_snapshot={
                "interests": [i.name for i in interests],
                "top_topics": learned_topics[:5],
            },
            decision={"plan_id": str(plan.id), "query_count": len(queries)},
            reason=f"Generated search plan with {len(queries)} queries from interests and learned topics",
            confidence=0.8,
        )
        self._db.add(event)
        await self._db.flush()

        logger.info(
            "search_plan_generated",
            user_id=str(user_id),
            plan_id=str(plan.id),
            queries=len(queries),
            trace_id=trace_id,
        )
        return plan

    async def _expand_queries(self, base_topics: List[str], profile) -> List[str]:
        """Use LLM to expand topics into specific search queries."""
        if not self._llm or not base_topics:
            # Fallback: use topics directly
            return base_topics[:10]

        try:
            expertise = profile.expertise_level if profile else "intermediate"
            prompt = f"""Generate specific search queries for a {expertise}-level researcher interested in:
{chr(10).join(f'- {t}' for t in base_topics[:8])}

Generate 8-12 specific, targeted search queries. Return as JSON array: ["query 1", "query 2", ...]
Focus on technical depth and recent developments."""

            response = await self._llm.generate(prompt, max_tokens=300)
            import json
            import re
            match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if match:
                queries = json.loads(match.group())
                return [str(q) for q in queries[:12]]
        except Exception as e:
            logger.warning("query_expansion_failed", error=str(e))

        return base_topics[:10]

    def _build_source_priorities(self, profile) -> List[str]:
        """Build source priority list based on user profile."""
        priorities = ["arxiv", "official_blogs"]
        if profile:
            if profile.preferred_depth == "deep":
                priorities = ["arxiv", "research_papers", "official_blogs", "documentation"]
            elif profile.expertise_level in ("beginner", "intermediate"):
                priorities = ["official_blogs", "tutorials", "documentation", "arxiv"]
        return priorities

    async def _load_interests(self, user_id: uuid.UUID) -> List[Interest]:
        result = await self._db.execute(
            select(Interest).where(Interest.user_id == user_id).order_by(Interest.weight.desc())
        )
        return list(result.scalars().all())

    async def _load_top_topic_preferences(self, user_id: uuid.UUID) -> List[UserTopicPreference]:
        result = await self._db.execute(
            select(UserTopicPreference)
            .where(UserTopicPreference.user_id == user_id)
            .order_by(UserTopicPreference.weight.desc())
            .limit(10)
        )
        return list(result.scalars().all())

    async def _load_profile(self, user_id: uuid.UUID):
        result = await self._db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
