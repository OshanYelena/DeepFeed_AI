"""
DeepFeed AI - Trace ID Middleware
Injects a unique trace_id into every request context.
All log entries and responses include this trace_id.
"""
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from logger import bind_trace_id, clear_context


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        bind_trace_id(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            clear_context()
