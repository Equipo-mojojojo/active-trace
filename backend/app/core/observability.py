from __future__ import annotations

from fastapi import FastAPI

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTEL_INSTALLED = True
except ImportError:
    trace = None
    OTLPSpanExporter = None
    FastAPIInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    OTEL_INSTALLED = False

from app.core.config import Settings

_instrumented_app_ids: set[int] = set()


def instrument_app(app: FastAPI, settings: Settings) -> None:
    if (
        not settings.OTEL_ENABLED
        or not OTEL_INSTALLED
        or id(app) in _instrumented_app_ids
    ):
        return

    resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
    tracer_provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT and OTLPSpanExporter is not None:
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(tracer_provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    _instrumented_app_ids.add(id(app))


def uninstrument_app(app: FastAPI) -> None:
    if not OTEL_INSTALLED or id(app) not in _instrumented_app_ids:
        return

    FastAPIInstrumentor.uninstrument_app(app)
    _instrumented_app_ids.remove(id(app))
