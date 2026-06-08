"""
DeepFeed AI - Rate Limiting Middleware (M17 Security Hardening)
Token bucket per IP per minute. TDS §15.6.
Uses in-memory store (swap for Redis in production).
"""
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import settings
from logger import get_logger

logger = get_logger(__name__)

# In-memory store: ip -> (tokens, last_refill_time)
_buckets: dict[str, tuple[float, float]] = defaultdict(lambda: (float(settings.rate_limit_per_minute), time.time()))
_BUCKET_CAPACITY = settings.rate_limit_per_minute
_REFILL_RATE = settings.rate_limit_per_minute / 60.0  # tokens per second

# Exempt paths (health, metrics, docs)
_EXEMPT_PATHS = {"/health", "/health/ready", "/metrics", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter per client IP.
    Default: 60 requests/minute per IP.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        trace_id = getattr(request.state, "trace_id", "")

        allowed, remaining = self._consume_token(client_ip)

        if not allowed:
            logger.warning("rate_limit_exceeded", ip=client_ip, path=request.url.path, trace_id=trace_id)
            return JSONResponse(
                status_code=429,
                content={
                    "trace_id": trace_id,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Max {settings.rate_limit_per_minute} requests/minute.",
                        "details": None,
                    },
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        return response

    def _consume_token(self, client_ip: str) -> tuple[bool, float]:
        """Token bucket: consume one token. Returns (allowed, remaining_tokens)."""
        now = time.time()
        tokens, last_refill = _buckets[client_ip]

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(_BUCKET_CAPACITY, tokens + elapsed * _REFILL_RATE)

        if tokens >= 1.0:
            tokens -= 1.0
            _buckets[client_ip] = (tokens, now)
            return True, tokens
        else:
            _buckets[client_ip] = (tokens, now)
            return False, 0.0
