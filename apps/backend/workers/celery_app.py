"""
DeepFeed AI - Celery Worker Configuration
Background processing for discovery, extraction, ranking, summarization, and adaptation.
All long-running operations run here — never in the API layer (TDS §9.1).
"""
import asyncio
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init, beat_init
from config import settings
from logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────
celery_app = Celery(
    "deepfeed",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    # Without this, the worker process never imports workers/tasks.py, so
    # none of the @celery_app.task decorators in it ever run and nothing
    # gets registered — `celery inspect registered` would report empty.
    include=["workers.tasks"],
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
    # Celery's built-in default queue is literally named "celery", which the
    # worker never listens on (-Q default,discovery,processing,ranking,adaptation).
    # These task_routes patterns previously used dotted-namespace globs
    # ("workers.tasks.discovery.*") that don't match any real task name
    # ("workers.tasks.run_discovery_task"), so every task fell through to
    # "celery" and sat there unconsumed. Route by the real task names, and
    # give anything unmatched an explicit home on a queue the worker actually
    # drains, instead of Celery's unconsumed default.
    task_default_queue="default",
    task_routes={
        "workers.tasks.run_discovery_task": {"queue": "discovery"},
        "workers.tasks.run_personalized_discovery_task": {"queue": "discovery"},
        "workers.tasks.run_processing_task": {"queue": "processing"},
        "workers.tasks.run_summarization_task": {"queue": "processing"},
        "workers.tasks.run_ranking_task": {"queue": "ranking"},
        "workers.tasks.run_adaptation_task": {"queue": "adaptation"},
        "workers.tasks.run_reflection_task": {"queue": "adaptation"},
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


# ── Metrics Exporters ─────────────────────────────────────────────────────────
# worker_init fires once in the main worker process, before it forks its
# prefork pool — exactly where the multiprocess-aggregating server needs to
# start (see workers/worker_metrics.py's docstring for why this can't just
# be a plain single-process exporter). This same module is also imported by
# `celery -A workers.celery_app beat`, where worker_init never fires and
# beat_init does instead, so both handlers can live here unconditionally.

@worker_init.connect
def _start_worker_metrics_server(**kwargs) -> None:
    from workers.worker_metrics import start_worker_metrics_server
    start_worker_metrics_server(port=9091)


@beat_init.connect
def _start_beat_metrics_server(**kwargs) -> None:
    # Beat doesn't execute task bodies itself (it only dispatches), so
    # there's no per-task business metric to report here — the default
    # process collectors (CPU, memory, GC, process start time) that
    # prometheus_client auto-registers are the useful signal: is beat
    # actually alive and not stuck.
    from prometheus_client import start_http_server
    start_http_server(9092)
