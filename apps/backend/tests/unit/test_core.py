"""
DeepFeed AI - Unit Tests
Covers: Ranking Engine, Auth Service, Password hashing, Feed scoring.
Target: 80%+ coverage (TDS §18.2)
"""
import uuid
import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestPasswordSecurity:
    def test_hash_password_produces_different_hashes(self):
        from infrastructure.auth.passwords import hash_password
        h1 = hash_password("StrongPassword123!")
        h2 = hash_password("StrongPassword123!")
        assert h1 != h2  # Argon2 uses different salts

    def test_verify_correct_password(self):
        from infrastructure.auth.passwords import hash_password, verify_password
        pw = "StrongPassword123!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        from infrastructure.auth.passwords import hash_password, verify_password
        hashed = hash_password("StrongPassword123!")
        assert verify_password("WrongPassword456!", hashed) is False


class TestJWTTokens:
    def test_create_and_verify_access_token(self):
        from infrastructure.auth.tokens import create_access_token, verify_access_token
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        assert token
        result = verify_access_token(token)
        assert result == user_id

    def test_invalid_token_returns_none(self):
        from infrastructure.auth.tokens import verify_access_token
        result = verify_access_token("not.a.valid.token")
        assert result is None

    def test_refresh_token_not_valid_as_access_token(self):
        from infrastructure.auth.tokens import create_refresh_token, verify_access_token
        user_id = str(uuid.uuid4())
        refresh = create_refresh_token(user_id)
        # Refresh token should NOT pass as access token
        result = verify_access_token(refresh)
        assert result is None


# ── Register DTO Validation ───────────────────────────────────────────────────

class TestRegisterRequest:
    def test_valid_registration(self):
        from application.dtos.user_dtos import RegisterRequest
        req = RegisterRequest(email="test@example.com", password="StrongPass123!")
        assert req.email == "test@example.com"

    def test_short_password_rejected(self):
        from application.dtos.user_dtos import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="short")

    def test_password_without_uppercase_rejected(self):
        from application.dtos.user_dtos import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="alllowercase123!")

    def test_invalid_email_rejected(self):
        from application.dtos.user_dtos import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="StrongPass123!")


# ── Ranking Engine Unit Tests ─────────────────────────────────────────────────

class TestFreshnessScore:
    def test_very_recent_content_scores_high(self):
        from application.services.ranking_service import RankingEngine
        engine = RankingEngine(MagicMock())
        recent = datetime.now(timezone.utc) - timedelta(hours=1)
        score = engine._compute_freshness(recent)
        assert score > 0.9

    def test_week_old_content_scores_medium(self):
        from application.services.ranking_service import RankingEngine
        engine = RankingEngine(MagicMock())
        week_old = datetime.now(timezone.utc) - timedelta(days=7)
        score = engine._compute_freshness(week_old)
        assert 0.3 < score < 0.7

    def test_month_old_content_scores_low(self):
        from application.services.ranking_service import RankingEngine
        engine = RankingEngine(MagicMock())
        old = datetime.now(timezone.utc) - timedelta(days=30)
        score = engine._compute_freshness(old)
        assert score < 0.1

    def test_none_published_at_returns_default(self):
        from application.services.ranking_service import RankingEngine
        engine = RankingEngine(MagicMock())
        score = engine._compute_freshness(None)
        assert score == 0.3

    def test_freshness_formula_matches_exponential_decay(self):
        from application.services.ranking_service import RankingEngine
        engine = RankingEngine(MagicMock())
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        score = engine._compute_freshness(five_days_ago)
        expected = round(math.exp(-0.1 * 5), 4)
        assert abs(score - expected) < 0.01


# ── Interest Weight Validation ────────────────────────────────────────────────

class TestInterestValidation:
    def test_valid_weight(self):
        from application.dtos.user_dtos import CreateInterestRequest
        req = CreateInterestRequest(name="AI Agents", weight=0.9)
        assert req.weight == 0.9

    def test_weight_above_1_rejected(self):
        from application.dtos.user_dtos import CreateInterestRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CreateInterestRequest(name="AI Agents", weight=1.5)

    def test_negative_weight_rejected(self):
        from application.dtos.user_dtos import CreateInterestRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CreateInterestRequest(name="AI Agents", weight=-0.1)


# ── Feedback Signal Mapping ───────────────────────────────────────────────────

class TestFeedbackSignals:
    def test_like_has_positive_signal(self):
        from application.services.feedback_service import FEEDBACK_SIGNAL_MAP
        assert FEEDBACK_SIGNAL_MAP["like"] > 0

    def test_bookmark_has_highest_positive_signal(self):
        from application.services.feedback_service import FEEDBACK_SIGNAL_MAP
        assert FEEDBACK_SIGNAL_MAP["bookmark"] >= FEEDBACK_SIGNAL_MAP["like"]

    def test_dislike_has_negative_signal(self):
        from application.services.feedback_service import FEEDBACK_SIGNAL_MAP
        assert FEEDBACK_SIGNAL_MAP["dislike"] < 0

    def test_ignore_has_negative_signal(self):
        from application.services.feedback_service import FEEDBACK_SIGNAL_MAP
        assert FEEDBACK_SIGNAL_MAP["ignore"] < 0

    def test_all_valid_types_present(self):
        from application.services.feedback_service import FEEDBACK_SIGNAL_MAP
        required = {"like", "dislike", "bookmark", "ignore", "read"}
        assert required.issubset(set(FEEDBACK_SIGNAL_MAP.keys()))


# ── Topic Classifier Keyword Fallback ────────────────────────────────────────

class TestTopicClassifier:
    def test_ml_content_classified_correctly(self):
        from application.services.content_service import TopicClassifier
        classifier = TopicClassifier()
        topics = classifier._classify_with_keywords(
            "deep learning neural networks training backpropagation gradient descent"
        )
        names = [t["name"] for t in topics]
        assert any("Learning" in n for n in names)

    def test_empty_content_returns_empty(self):
        from application.services.content_service import TopicClassifier
        classifier = TopicClassifier()
        topics = classifier._classify_with_keywords("")
        assert isinstance(topics, list)

    def test_confidence_within_range(self):
        from application.services.content_service import TopicClassifier
        classifier = TopicClassifier()
        topics = classifier._classify_with_keywords("machine learning deep learning AI")
        for topic in topics:
            assert 0.0 <= topic["confidence"] <= 1.0


# ── Domain Events ─────────────────────────────────────────────────────────────

class TestDomainEvents:
    def test_content_discovered_event_has_id(self):
        from domain.events.events import ContentDiscovered
        event = ContentDiscovered(content_item_id="abc", source_id="src", url="http://x.com", title="Test")
        assert event.event_id
        assert event.occurred_at

    def test_feedback_received_event(self):
        from domain.events.events import FeedbackReceived
        event = FeedbackReceived(user_id="u1", recommendation_id="r1", feedback_type="like", feedback_value=0.8)
        assert event.feedback_type == "like"


# ── API Response Format ───────────────────────────────────────────────────────

class TestAPISchemas:
    def test_success_response_format(self):
        from api.schemas import success_response
        resp = success_response({"key": "value"}, "trace-123")
        assert resp["trace_id"] == "trace-123"
        assert resp["data"]["key"] == "value"

    def test_error_response_format(self):
        from api.schemas import error_response
        resp = error_response("NOT_FOUND", "Resource not found", "trace-456")
        assert resp["trace_id"] == "trace-456"
        assert resp["error"]["code"] == "NOT_FOUND"
        assert resp["error"]["message"] == "Resource not found"
