"""
DeepFeed AI - Database Models
All SQLAlchemy ORM models matching the TDS database schema exactly.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Text, Float, Boolean, Integer, ForeignKey,
    TIMESTAMP, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database.connection import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False)
    interests: Mapped[List["Interest"]] = relationship("Interest", back_populates="user")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="user")
    feedback: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user")
    interest_signals: Mapped[List["UserInterestSignal"]] = relationship("UserInterestSignal", back_populates="user")
    topic_preferences: Mapped[List["UserTopicPreference"]] = relationship("UserTopicPreference", back_populates="user")
    source_preferences: Mapped[List["SourcePreference"]] = relationship("SourcePreference", back_populates="user")
    search_plans: Mapped[List["SearchPlan"]] = relationship("SearchPlan", back_populates="user")
    adaptation_events: Mapped[List["AdaptationEvent"]] = relationship("AdaptationEvent", back_populates="user")
    reflection_reports: Mapped[List["ReflectionReport"]] = relationship("ReflectionReport", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    expertise_level: Mapped[str] = mapped_column(String(20), nullable=False, default="intermediate")
    preferred_depth: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    preferred_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="interests")


# ── Sources & Content ─────────────────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    content_items: Mapped[List["ContentItem"]] = relationship("ContentItem", back_populates="source")
    source_preferences: Mapped[List["SourcePreference"]] = relationship("SourcePreference", back_populates="source")


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    author: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, default="article")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="discovered")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    source: Mapped["Source"] = relationship("Source", back_populates="content_items")
    processed_content: Mapped[Optional["ProcessedContent"]] = relationship("ProcessedContent", back_populates="content_item", uselist=False)
    content_topics: Mapped[List["ContentTopic"]] = relationship("ContentTopic", back_populates="content_item")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="content_item")
    summaries: Mapped[Optional["Summary"]] = relationship("Summary", back_populates="content_item", uselist=False)
    interest_signals: Mapped[List["UserInterestSignal"]] = relationship("UserInterestSignal", back_populates="content_item")

    __table_args__ = (
        Index("idx_content_items_canonical_url", "canonical_url"),
        Index("idx_content_items_source_id", "source_id"),
        Index("idx_content_items_status", "status"),
    )


class ProcessedContent(Base):
    __tablename__ = "processed_contents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    clean_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    content_item: Mapped["ContentItem"] = relationship("ContentItem", back_populates="processed_content")


class ContentTopic(Base):
    __tablename__ = "content_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    content_item: Mapped["ContentItem"] = relationship("ContentItem", back_populates="content_topics")


# ── Recommendations ───────────────────────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    content_item: Mapped["ContentItem"] = relationship("ContentItem", back_populates="recommendations")
    trace: Mapped[Optional["RecommendationTrace"]] = relationship("RecommendationTrace", back_populates="recommendation", uselist=False)
    feedback: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="recommendation")

    __table_args__ = (
        Index("idx_recommendations_user_id", "user_id"),
        Index("idx_recommendations_final_score", "final_score"),
    )


class RecommendationTrace(Base):
    __tablename__ = "recommendation_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, unique=True)
    matched_interests: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    scoring_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="trace")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_short: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_detailed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_takeaways: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="fallback")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    content_item: Mapped["ContentItem"] = relationship("ContentItem", back_populates="summaries")


# ── Feedback ──────────────────────────────────────────────────────────────────

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    feedback_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="feedback")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="feedback")

    __table_args__ = (
        Index("idx_feedback_user_id", "user_id"),
    )


# ── Agentic Adaptation ────────────────────────────────────────────────────────

class UserInterestSignal(Base):
    __tablename__ = "user_interest_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="interest_signals")
    content_item: Mapped["ContentItem"] = relationship("ContentItem", back_populates="interest_signals")


class UserTopicPreference(Base):
    __tablename__ = "user_topic_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="explicit")
    first_detected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="topic_preferences")

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_user_topic"),
        Index("idx_user_topic_preferences_user_id", "user_id"),
    )


class SourcePreference(Base):
    __tablename__ = "source_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    personal_trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    interaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_feedback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    negative_feedback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="source_preferences")
    source: Mapped["Source"] = relationship("Source", back_populates="source_preferences")

    __table_args__ = (
        UniqueConstraint("user_id", "source_id", name="uq_user_source"),
    )


class SearchPlan(Base):
    __tablename__ = "search_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(100), nullable=False)
    queries: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_priorities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    search_depth: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="search_plans")

    __table_args__ = (
        Index("idx_search_plans_user_id", "user_id"),
    )


class AdaptationEvent(Base):
    __tablename__ = "adaptation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    decision: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="adaptation_events")

    __table_args__ = (
        Index("idx_adaptation_events_user_id", "user_id"),
    )


class ReflectionReport(Base):
    __tablename__ = "reflection_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_period: Mapped[str] = mapped_column(String(20), nullable=False)
    insights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recommendations_: Mapped[Optional[dict]] = mapped_column("recommendations", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="reflection_reports")


# ── Discovery Runs ────────────────────────────────────────────────────────────
# One row per *manual* discovery trigger. The hourly cron is not recorded
# here — it's tracked via Celery's own task log. We only need this table
# to enforce the per-user daily quota and surface "what just happened" to
# the UI (last run time, item count, currently-running task).
class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Celery task id — opaque string. Indexed because the status endpoint
    # looks runs up by this.
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # 'pending' | 'running' | 'completed' | 'failed'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # 'personalized' | 'global' — leaves room for the global variant later.
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False, default="personalized")
    # Queries we actually sent into discovery, persisted for debugging.
    search_queries: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Number of net-new ContentItems created by this run. Populated on completion.
    new_items_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=now_utc, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    __table_args__ = (
        # Quota check: "how many runs has this user started in the last 24h?"
        # Range scan on (user_id, started_at) is the right shape.
        Index("idx_discovery_runs_user_started", "user_id", "started_at"),
        Index("idx_discovery_runs_status", "status"),
    )
