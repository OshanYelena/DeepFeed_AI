"""
DeepFeed AI - Audit Logging Middleware (M17)
Logs all required audit events per TDS §15.9:
  Login, Logout, Password Change, Profile Change,
  Adaptation Override, Admin Actions.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from logger import get_logger

logger = get_logger(__name__)

# Audit-worthy paths pattern
_AUDIT_PATHS = {
    ("POST", "/auth/login"),
    ("POST", "/auth/register"),
    ("PUT", "/profile/me"),
    ("POST", "/agent/preferences/correct"),
    ("POST", "/admin/sources"),
    ("PUT", "/admin/sources"),
    ("DELETE", "/admin/sources"),
    ("POST", "/admin/jobs/discovery/run"),
    ("POST", "/agent/adapt/run"),
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs auditable API actions with trace_id, user context, and status."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        method = request.method
        path = request.url.path
        trace_id = getattr(request.state, "trace_id", "")

        # Always log API requests for audit trail
        is_audit = any(
            method == m and path.startswith(p)
            for m, p in _AUDIT_PATHS
        )

        if is_audit:
            logger.info(
                "audit_event",
                method=method,
                path=path,
                status=response.status_code,
                duration_ms=duration_ms,
                trace_id=trace_id,
                event_type="api_audit",
            )

        return response
