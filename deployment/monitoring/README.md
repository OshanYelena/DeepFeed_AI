# Monitoring

## Scrape targets

| Job | Target | What it covers |
|---|---|---|
| `deepfeed_backend` | `backend:8000/metrics` | App-level counters/histograms defined in `infrastructure/observability/metrics.py` — discovery, processing, ranking, adaptation, LLM calls, HTTP requests. Populated by `.inc()`/`.observe()` calls added throughout the service layer (ranking_service.py, discovery_service.py, content_service.py, the agent classes, llm/providers.py) plus `api/middleware/metrics.py` for the HTTP-level ones. |
| `deepfeed_worker` | `worker:9091` | The same `deepfeed_*` metrics, but for whatever the Celery worker executes on its own (the beat-scheduled hourly discovery / 30-min processing / daily adaptation-reflection jobs — the user-triggered "Discover Now" path runs synchronously in the backend process instead, per an earlier fix, so it shows up under `deepfeed_backend`, not here). |
| `deepfeed_beat` | `beat:9092` | Process liveness only (default `prometheus_client` process collectors — CPU, memory, uptime). Beat dispatches task messages, it doesn't execute task bodies, so there's no business metric to report from it — the useful signal is just whether it's alive, since a silently-stalled beat means nothing runs automatically with no other symptom. |
| `postgres` | `postgres_exporter:9187` | Standard Postgres server metrics (connections, transaction rates, etc.) via `prometheuscommunity/postgres-exporter`. |
| `rabbitmq` | `rabbitmq:15692` | Queue depths, message rates, consumer counts, via RabbitMQ's own `rabbitmq_prometheus` plugin (enabled through `deployment/docker/rabbitmq/enabled_plugins` — see that file's comment for why it also has to list `rabbitmq_management`). |
| `prometheus` | `prometheus:9090` | Prometheus monitoring itself. |

## Why the worker and beat have their own exporters

`RankingEngine`, `DiscoveryService`, etc. run in two different processes: synchronously inside the backend (the primary, user-triggered path) and inside the Celery worker (the beat-scheduled background jobs). A plain in-memory Prometheus registry in the worker process is invisible to the backend's `/metrics` endpoint — they're different containers. Worse, the worker itself is a 4-process prefork pool, so even a worker-local exporter needs to aggregate across those 4 children, not just expose one process's view. `workers/worker_metrics.py` handles this using `prometheus_client`'s documented multiprocess mode (`PROMETHEUS_MULTIPROC_DIR`), started once in the parent process via Celery's `worker_init` signal (not `worker_process_init`, which fires once per forked child and would try to bind the same port four times).

## Verifying it's actually working

After bringing the stack up and generating some real traffic (log in, click **Discover Now**, submit feedback, run an adaptation cycle):

- Prometheus → **Status → Targets**: all 6 jobs above should show **UP**.
- Query `deepfeed_recommendations_generated_total` or `deepfeed_llm_requests_total` directly in Prometheus's Graph tab — should be non-zero.
- Grafana's "System Health" dashboard should show real numbers, not flat zero lines, across every panel including the Infrastructure row.

If a target shows **DOWN**: for `rabbitmq`, double check the plugin actually loaded (`docker exec deepfeed_rabbitmq rabbitmq-plugins list` — `rabbitmq_prometheus` should show `[E*]`); for `worker`, check `docker logs deepfeed_worker` for `worker_metrics_server_started` — if it's missing, `PROMETHEUS_MULTIPROC_DIR` likely isn't set in that container's environment.
