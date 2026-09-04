"""
DeepFeed AI - Celery Worker Metrics Exporter

The FastAPI backend's own infrastructure/observability/metrics.py uses a
plain in-memory CollectorRegistry, which works because it's one process.
The worker is a prefork pool (default concurrency=4) — four child
processes, each with its own memory. A plain in-memory registry in one
child would never see what the other three did, and the backend's
/metrics endpoint can't see any of them (they're a different container
entirely). Prometheus's own answer to this is "multiprocess mode": every
process writes its metric deltas to files in PROMETHEUS_MULTIPROC_DIR
(set as an env var — see docker-compose.yml's worker service — which is
what actually makes the Counter/Histogram objects imported by the shared
service layer switch into multiprocess-safe mode; nothing here does that
part), and one process aggregates those files on scrape.

This module is that aggregator: a tiny HTTP server, started once in the
worker's main process (see celery_app.py's worker_init handler — NOT
worker_process_init, which fires once per forked child and would try to
bind this same port four times), exposing everything the multiprocess
directory currently holds.
"""
import os
import threading
from wsgiref.simple_server import make_server

from logger import get_logger

logger = get_logger(__name__)

_server_thread = None


def start_worker_metrics_server(port: int = 9091) -> None:
    """Start the aggregating /metrics HTTP server in a background thread.
    Safe to call more than once — only the first call in a given process
    actually starts anything. No-ops (with a warning) if
    PROMETHEUS_MULTIPROC_DIR isn't set, since multiprocess mode needs it
    for the metric objects themselves to have written anything to read.
    """
    global _server_thread
    if _server_thread is not None:
        return

    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not multiproc_dir:
        logger.warning(
            "worker_metrics_server_skipped",
            reason="PROMETHEUS_MULTIPROC_DIR not set",
        )
        return

    # prometheus_client writes per-process metric files here but doesn't
    # create the directory itself — and this runs in worker_init, before
    # any forked child could otherwise race to create it first.
    os.makedirs(multiproc_dir, exist_ok=True)

    from prometheus_client import CollectorRegistry, make_wsgi_app, multiprocess

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    app = make_wsgi_app(registry)

    httpd = make_server("", port, app)
    _server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    _server_thread.start()
    logger.info("worker_metrics_server_started", port=port)
