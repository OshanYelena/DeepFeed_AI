"""
DeepFeed AI - Domain Events
All events emitted by the system as defined in the SAD.
Events are the primary communication mechanism between modules.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
import uuid


def event_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BaseEvent:
    event_id: str = field(default_factory=event_id)
    occurred_at: datetime = field(default_factory=now_utc)
    trace_id: Optional[str] = None


# ── Discovery Events ──────────────────────────────────────────────────────────

@dataclass
class ContentDiscovered(BaseEvent):
    content_item_id: str = ""
    source_id: str = ""
    url: str = ""
    title: str = ""


@dataclass
class ContentExtractionFailed(BaseEvent):
    content_item_id: str = ""
    reason: str = ""


@dataclass
class ContentExtracted(BaseEvent):
    content_item_id: str = ""
    word_count: int = 0
    extraction_quality: str = "medium"


@dataclass
class ContentClassified(BaseEvent):
    content_item_id: str = ""
    topics: list[dict] = field(default_factory=list)


@dataclass
class ContentEvaluated(BaseEvent):
    content_item_id: str = ""
    quality_score: float = 0.0


@dataclass
class ContentRanked(BaseEvent):
    user_id: str = ""
    recommendation_id: str = ""
    final_score: float = 0.0
    rank_position: int = 0


@dataclass
class SummaryGenerated(BaseEvent):
    content_item_id: str = ""
    generated_by: str = "model"


@dataclass
class FeedUpdated(BaseEvent):
    user_id: str = ""
    item_count: int = 0


# ── Feedback Events ───────────────────────────────────────────────────────────

@dataclass
class FeedbackReceived(BaseEvent):
    user_id: str = ""
    recommendation_id: str = ""
    feedback_type: str = ""
    feedback_value: float = 0.0


# ── Agentic Events ────────────────────────────────────────────────────────────

@dataclass
class AdaptationTriggered(BaseEvent):
    user_id: str = ""
    trigger: str = ""
    mode: str = "full"


@dataclass
class SearchPlanGenerated(BaseEvent):
    user_id: str = ""
    search_plan_id: str = ""
    query_count: int = 0


@dataclass
class ReflectionCompleted(BaseEvent):
    user_id: str = ""
    report_id: str = ""
    period: str = "daily"
    insight_count: int = 0
