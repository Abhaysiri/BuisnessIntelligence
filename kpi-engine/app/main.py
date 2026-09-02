from fastapi import FastAPI

from app.schemas.movement import KPIMovementEvent
from app.services.diagnostic import run_investigation
from app.api.persona import router as persona_router
from app.api.middleware import TelemetryMiddleware
from app.api.routes import router as ingestion_router

from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(
    title="KPI Intelligence Engine",
    description="Governed KPI Intelligence-to-Action Engine API",
    version="1.0.0"
)

# Enable CORS for the frontend React application
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hook 1: Request Lifecycle & Observability Middleware
api.add_middleware(TelemetryMiddleware)

# Include Routers
api.include_router(persona_router, tags=["Persona Storytelling"])
api.include_router(ingestion_router)

from app.api.documents import router as documents_router
api.include_router(documents_router)

from app.api.audit import router as audit_router
api.include_router(audit_router)

# OpenTelemetry Setup
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter, SpanExportResult
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    import json
    
    class SupabaseSpanExporter(SpanExporter):
        def export(self, spans):
            try:
                from app.tools.database import engine
                from sqlalchemy import text
                with engine.begin() as conn:
                    for span in spans:
                        conn.execute(
                            text("""
                                INSERT INTO public.telemetry_traces 
                                (trace_id, span_id, name, status_code, status_description, start_time, end_time, attributes, events) 
                                VALUES (:trace_id, :span_id, :name, :status_code, :status_description, to_timestamp(:start_time), to_timestamp(:end_time), :attributes, :events)
                            """),
                            {
                                "trace_id": format(span.context.trace_id, "032x"),
                                "span_id": format(span.context.span_id, "016x"),
                                "name": span.name,
                                "status_code": span.status.status_code.name if span.status else "UNSET",
                                "status_description": span.status.description if span.status else "",
                                "start_time": span.start_time / 1e9 if span.start_time else 0,
                                "end_time": span.end_time / 1e9 if span.end_time else 0,
                                "attributes": json.dumps(dict(span.attributes) if span.attributes else {}),
                                "events": json.dumps([{"name": e.name, "timestamp": e.timestamp} for e in span.events] if span.events else [])
                            }
                        )
            except Exception as e:
                print("Failed to export span to Supabase:", e)
            return SpanExportResult.SUCCESS

    # Set up global tracer provider
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    supabase_processor = BatchSpanProcessor(SupabaseSpanExporter())
    provider.add_span_processor(processor)
    provider.add_span_processor(supabase_processor)
    trace.set_tracer_provider(provider)

    # Instrument the FastAPI app
    FastAPIInstrumentor.instrument_app(api)
    print("OpenTelemetry instrumentation initialized.")
except ImportError:
    print("OpenTelemetry packages not found. Skipping OTel instrumentation.")


@api.get("/health")
def health_check():
    return {"status": "healthy", "service": "kpi-engine"}


@api.post("/investigations")
def investigate(event: KPIMovementEvent):
    payload = run_investigation(event)
    return payload

app = api