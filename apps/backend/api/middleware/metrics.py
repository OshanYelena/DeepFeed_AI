"""
DeepFeed AI - HTTP Metrics Middleware
Records deepfeed_http_requests_total / deepfeed_http_request_duration_seconds
for every request, same BaseHTTPMiddleware pattern as TraceIDMiddleware.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.observability.metrics import http_requests_total, http_request_duration_seconds


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started_at = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - started_at

        # Use the matched route's template ("/feed/{recommendation_id}"),
        # not the raw resolved path — otherwise every distinct UUID in the
        # URL becomes its own label value and the metric's cardinality
        # grows without bound. Falls back to the raw path for requests
        # that never matched a route (404s).
        route = request.scope.get("route")
        endpoint = route.path if route is not None else request.url.path

        labels = {"method": request.method, "endpoint": endpoint}
        http_requests_total.labels(**labels, status=str(response.status_code)).inc()
        http_request_duration_seconds.labels(**labels).observe(duration)

        return response
