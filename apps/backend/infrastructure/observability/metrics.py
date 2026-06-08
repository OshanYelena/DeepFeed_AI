"""
DeepFeed AI - Prometheus Metrics (M16 Observability)
All required metrics from TDS §16.3.
Exposes /metrics endpoint via prometheus_client.
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

# ── Registry ──────────────────────────────────────────────────────────────────
REGISTRY = CollectorRegistry()

# ── Discovery Metrics (TDS §16.3) ─────────────────────────────────────────────
discovery_jobs_total = Counter(
    "deepfeed_discovery_jobs_total",
    "Total number of discovery jobs run",
    registry=REGISTRY,
)
items_discovered_total = Counter(
    "deepfeed_items_discovered_total",
    "Total content items discovered",
    registry=REGISTRY,
)
provider_failures_total = Counter(
    "deepfeed_provider_failures_total",
    "Total provider failures during discovery",
    ["provider"],
    registry=REGISTRY,
)
discovery_duration_seconds = Histogram(
    "deepfeed_discovery_duration_seconds",
    "Discovery job duration in seconds",
    registry=REGISTRY,
)

# ── Processing Metrics ────────────────────────────────────────────────────────
extraction_success_total = Counter(
    "deepfeed_extraction_success_total",
    "Total successful content extractions",
    registry=REGISTRY,
)
extraction_failure_total = Counter(
    "deepfeed_extraction_failure_total",
    "Total failed content extractions",
    registry=REGISTRY,
)
processing_duration_seconds = Histogram(
    "deepfeed_processing_duration_seconds",
    "Content processing duration in seconds",
    registry=REGISTRY,
)

# ── Recommendation Metrics ────────────────────────────────────────────────────
recommendations_generated_total = Counter(
    "deepfeed_recommendations_generated_total",
    "Total recommendations generated",
    registry=REGISTRY,
)
avg_relevance_score = Gauge(
    "deepfeed_avg_relevance_score",
    "Average relevance score of recent recommendations",
    registry=REGISTRY,
)
feed_size_gauge = Gauge(
    "deepfeed_feed_size",
    "Current average feed size",
    registry=REGISTRY,
)

# ── Adaptation Metrics ────────────────────────────────────────────────────────
adaptation_events_total = Counter(
    "deepfeed_adaptation_events_total",
    "Total adaptation events created",
    ["agent_name"],
    registry=REGISTRY,
)
topic_updates_total = Counter(
    "deepfeed_topic_updates_total",
    "Total topic preference updates",
    registry=REGISTRY,
)
source_updates_total = Counter(
    "deepfeed_source_updates_total",
    "Total source preference updates",
    registry=REGISTRY,
)
reflection_runs_total = Counter(
    "deepfeed_reflection_runs_total",
    "Total reflection runs completed",
    registry=REGISTRY,
)

# ── LLM Metrics ───────────────────────────────────────────────────────────────
llm_requests_total = Counter(
    "deepfeed_llm_requests_total",
    "Total LLM requests made",
    ["provider"],
    registry=REGISTRY,
)
llm_tokens_used_total = Counter(
    "deepfeed_llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["provider"],
    registry=REGISTRY,
)
llm_request_duration_seconds = Histogram(
    "deepfeed_llm_request_duration_seconds",
    "LLM request latency in seconds",
    ["provider"],
    registry=REGISTRY,
)
llm_failures_total = Counter(
    "deepfeed_llm_failures_total",
    "Total LLM request failures",
    ["provider"],
    registry=REGISTRY,
)

# ── API Metrics ───────────────────────────────────────────────────────────────
http_requests_total = Counter(
    "deepfeed_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)
http_request_duration_seconds = Histogram(
    "deepfeed_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=REGISTRY,
)

# ── Metrics Endpoint ──────────────────────────────────────────────────────────
router = APIRouter(tags=["Observability"])


@router.get("/metrics")
async def metrics():
    """Prometheus metrics scrape endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
