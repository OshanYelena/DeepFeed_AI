"""
DeepFeed AI - OpenTelemetry Tracing Setup (M16)
Distributed tracing per TDS §16.4.
Every request generates a trace_id that propagates through:
  API → Worker → Database → LLM
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from config import settings
from logger import get_logger

logger = get_logger(__name__)
_tracer: trace.Tracer | None = None


def setup_tracing(app=None) -> None:
    """Initialize OpenTelemetry tracing. Call once at startup."""
    global _tracer

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "1.0.0",
        "deployment.environment": settings.app_env,
    })

    provider = TracerProvider(resource=resource)

    # Try to configure OTLP exporter if endpoint is set
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("otel_exporter_configured", endpoint=settings.otel_exporter_otlp_endpoint)
    except Exception as e:
        logger.warning("otel_exporter_not_configured", reason=str(e))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("deepfeed-ai")

    # Auto-instrument FastAPI and SQLAlchemy
    if app:
        FastAPIInstrumentor.instrument_app(app)

    logger.info("otel_tracing_initialized", service=settings.otel_service_name)


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("deepfeed-ai")
    return _tracer
