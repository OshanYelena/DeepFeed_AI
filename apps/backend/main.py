"""
DeepFeed AI - FastAPI Application
Full application factory with all phases integrated.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from logger import configure_logging, get_logger
from api.middleware.trace import TraceIDMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.middleware.audit import AuditMiddleware
from api.middleware.metrics import MetricsMiddleware
from api.routes.health import router as health_router
from api.routes.auth import router as auth_router
from api.routes.users import profile_router, interests_router
from api.routes.feed import router as feed_router
from api.routes.admin import feedback_router, admin_router
from api.routes.agent import router as agent_router
from api.routes.content import router as content_router
from api.routes.stats import router as stats_router
from infrastructure.observability.metrics import router as metrics_router

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepFeed AI",
        description="AI-powered personalized knowledge discovery — Discover signal. Ignore noise.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    # Starlette wraps these in reverse registration order — the last one
    # added becomes the outermost layer and runs first on the way in (see
    # TraceIDMiddleware's usage elsewhere in this codebase for why that
    # matters to RateLimit/Audit). MetricsMiddleware is added last on
    # purpose: it should see every request's final status code, including
    # ones CORS/RateLimit/Audit reject before the route ever runs.
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TraceIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://frontend:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(MetricsMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(interests_router)
    app.include_router(feed_router)
    app.include_router(feedback_router)
    app.include_router(admin_router)
    app.include_router(agent_router)
    app.include_router(content_router)
    app.include_router(stats_router)

    # ── Global Error Handler ──────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            trace_id=trace_id,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "trace_id": trace_id,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": None,
                },
            },
        )

    @app.on_event("startup")
    async def startup() -> None:
        logger.info("deepfeed_ai_starting", env=settings.app_env, version="1.0.0")
        try:
            from infrastructure.observability.tracing import setup_tracing
            setup_tracing(app)
        except Exception as e:
            logger.warning("tracing_setup_failed", error=str(e))

    @app.on_event("shutdown")
    async def shutdown() -> None:
        logger.info("deepfeed_ai_shutting_down")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.app_debug)
