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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hook 1: Request Lifecycle & Observability Middleware
api.add_middleware(TelemetryMiddleware)

# Include Routers
api.include_router(persona_router, tags=["Persona Storytelling"])
api.include_router(ingestion_router)


@api.get("/health")
def health_check():
    return {"status": "healthy", "service": "kpi-engine"}


@api.post("/investigations")
def investigate(event: KPIMovementEvent):
    payload = run_investigation(event)
    return payload