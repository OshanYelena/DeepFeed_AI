"""
DeepFeed AI - Reflection Agent (M14) & Adaptation Engine (M15)
Reflection: analyzes recommendation performance, generates reports.
Adaptation Engine: orchestrates all agents in a full adaptation cycle.
All decisions traceable via AdaptationEvents.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from infrastructure.database.models import (
    Feedback, Recommendation, ReflectionReport, AdaptationEvent,
    UserTopicPreference, SourcePreference,
)
from domain.interfaces.llm_provider import LLMProvider
from application.services.agents.user_modeling_agent import UserModelingAgent
from application.services.agents.research_planning_agent import ResearchPlanningAgent
from logger import get_logger

logger = get_logger(__name__)

REFLECTION_AGENT = "ReflectionAgent"
ADAPTATION_ENGINE = "AdaptationEngine"


class ReflectionAgent:
    """
    Evaluates recommendation performance and generates insight reports.
    Runs daily/weekly as per TDS §13.4.
    """

    def __init__(self, db: AsyncSession, llm_provider: Optional[LLMProvider] = None) -> None:
        self._db = db
        self._llm = llm_provider

    async def run(
        self,
        user_id: uuid.UUID,
        period: str = "daily",
        trace_id: str = "",
    ) -> ReflectionReport:
        """Run reflection analysis and return a ReflectionReport."""
        logger.info("reflection_agent_start", user_id=str(user_id), period=period, trace_id=trace_id)

        window = timedelta(days=1) if period == "daily" else timedelta(days=7)
        since = datetime.now(timezone.utc) - window

        # Gather performance metrics
        metrics = await self._gather_metrics(user_id, since)
        insights = await self._generate_insights(user_id, metrics)
        recommendations = await self._generate_recommendations(user_id, metrics)

        report = ReflectionReport(
            user_id=user_id,
            report_period=period,
            insights=insights,
            recommendations_=recommendations,
        )
        self._db.add(report)
        await self._db.flush()

        # Record adaptation event
        event = AdaptationEvent(
            user_id=user_id,
            agent_name=REFLECTION_AGENT,
            event_type="reflection_completed",
            input_snapshot={"metrics": metrics, "period": period},
            decision={"report_id": str(report.id), "insight_count": len(insights.get("insights", []))},
            reason=f"{period} reflection on recommendation performance",
            confidence=0.85,
        )
        self._db.add(event)
        await self._db.flush()

        logger.info("reflection_complete", user_id=str(user_id), report_id=str(report.id), trace_id=trace_id)
        return report

    async def _gather_metrics(self, user_id: uuid.UUID, since: datetime) -> dict:
        """Collect quantitative performance metrics."""
        # Total recommendations in period
        total_result = await self._db.execute(
            select(func.count(Recommendation.id)).where(
                and_(Recommendation.user_id == user_id, Recommendation.generated_at >= since)
            )
        )
        total = total_result.scalar() or 0

        # Feedback breakdown
        feedback_result = await self._db.execute(
            select(Feedback.feedback_type, func.count(Feedback.id))
            .join(Recommendation)
            .where(
                and_(Feedback.user_id == user_id, Feedback.created_at >= since)
            )
            .group_by(Feedback.feedback_type)
        )
        feedback_counts = {row[0]: row[1] for row in feedback_result.all()}

        # Average score
        avg_result = await self._db.execute(
            select(func.avg(Recommendation.final_score)).where(
                and_(Recommendation.user_id == user_id, Recommendation.generated_at >= since)
            )
        )
        avg_score = float(avg_result.scalar() or 0)

        likes = feedback_counts.get("like", 0) + feedback_counts.get("bookmark", 0)
        dislikes = feedback_counts.get("dislike", 0) + feedback_counts.get("ignore", 0)
        acceptance_rate = likes / total if total > 0 else 0

        return {
            "total_recommendations": total,
            "feedback_counts": feedback_counts,
            "avg_final_score": round(avg_score, 3),
            "acceptance_rate": round(acceptance_rate, 3),
            "likes": likes,
            "dislikes": dislikes,
        }

    async def _generate_insights(self, user_id: uuid.UUID, metrics: dict) -> dict:
        """Generate qualitative insights from metrics."""
        insights = []
        acceptance = metrics.get("acceptance_rate", 0)

        if acceptance >= 0.4:
            insights.append("Recommendation quality is high — users are engaging well.")
        elif acceptance >= 0.2:
            insights.append("Recommendation quality is moderate — consider refining topic weights.")
        else:
            insights.append("Low engagement — user interests may need recalibration.")

        if metrics.get("dislikes", 0) > metrics.get("likes", 1) * 2:
            insights.append("High dislike rate detected — topic preferences may have drifted.")

        if metrics.get("total_recommendations", 0) < 5:
            insights.append("Low recommendation volume — discovery pipeline may need expansion.")

        return {
            "insights": insights,
            "metrics_summary": metrics,
            "period_analyzed": "daily",
        }

    async def _generate_recommendations(self, user_id: uuid.UUID, metrics: dict) -> dict:
        """Generate actionable recommendations for adaptation."""
        actions = []
        acceptance = metrics.get("acceptance_rate", 0)

        if acceptance < 0.2:
            actions.append({
                "action": "expand_sources",
                "reason": "Low acceptance rate suggests current sources aren't matching interests",
                "priority": "high",
            })
            actions.append({
                "action": "recalibrate_topic_weights",
                "reason": "Topic weights may not reflect current interests",
                "priority": "high",
            })

        if metrics.get("dislikes", 0) > 3:
            actions.append({
                "action": "suppress_low_signal_sources",
                "reason": "Multiple dislikes indicate poor source quality for this user",
                "priority": "medium",
            })

        return {"recommended_actions": actions}


class AdaptationEngine:
    """
    Orchestrates the full adaptation cycle (TDS §13.3).
    Coordinates: UserModelingAgent → ResearchPlanningAgent → ReflectionAgent.
    Agentic loop: Observe → Interpret → Decide → Act → Learn
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        self._db = db
        self._llm = llm_provider
        self._user_modeling = UserModelingAgent(db)
        self._research_planning = ResearchPlanningAgent(db, llm_provider)
        self._reflection = ReflectionAgent(db, llm_provider)

    async def run_full_cycle(self, user_id: uuid.UUID, trace_id: str = "") -> dict:
        """
        Execute full adaptation cycle for one user.
        Returns summary of all changes.
        """
        logger.info("adaptation_cycle_start", user_id=str(user_id), trace_id=trace_id)

        summary = {}

        # 1. Observe + Interpret: Update user model from signals
        modeling_result = await self._user_modeling.run(user_id, trace_id)
        summary["user_modeling"] = modeling_result

        # 2. Decide + Act: Generate new search plan
        plan = await self._research_planning.generate_search_plan(user_id, trace_id)
        summary["search_plan_id"] = str(plan.id)

        # 3. Learn: Run reflection
        report = await self._reflection.run(user_id, "daily", trace_id)
        summary["reflection_report_id"] = str(report.id)

        # Record engine-level event
        event = AdaptationEvent(
            user_id=user_id,
            agent_name=ADAPTATION_ENGINE,
            event_type="full_cycle_completed",
            input_snapshot=None,
            decision=summary,
            reason="Full adaptation cycle executed: user modeling, search planning, and reflection",
            confidence=0.9,
        )
        self._db.add(event)
        await self._db.flush()

        logger.info("adaptation_cycle_complete", user_id=str(user_id), summary=summary, trace_id=trace_id)
        return summary
