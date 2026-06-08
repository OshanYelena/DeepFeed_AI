"""
DeepFeed AI - Celery Worker Configuration
Background processing for discovery, extraction, ranking, summarization, and adaptation.
All long-running operations run here — never in the API layer (TDS §9.1).
"""
import asyncio
from celery import Celery
from celery.schedules import crontab
from config import settings
from logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────
celery_app = Celery(
    "deepfeed",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,
    task_default_retry_delay=30,  # 30 seconds initial retry
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.tasks.discovery.*": {"queue": "discovery"},
        "workers.tasks.processing.*": {"queue": "processing"},
        "workers.tasks.ranking.*": {"queue": "ranking"},
        "workers.tasks.adaptation.*": {"queue": "adaptation"},
    },
)

# ── Periodic Task Schedule ────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "run-discovery-every-hour": {
        "task": "workers.tasks.run_discovery_task",
        "schedule": crontab(minute=0),  # Every hour
    },
    "run-processing-every-30min": {
        "task": "workers.tasks.run_processing_task",
        "schedule": crontab(minute="*/30"),
    },
    "run-adaptation-daily": {
        "task": "workers.tasks.run_adaptation_task",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "run-reflection-daily": {
        "task": "workers.tasks.run_reflection_task",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
    },
}
