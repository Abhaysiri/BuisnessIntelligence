from fastapi import FastAPI

from app.schemas.movement import KPIMovementEvent
from app.services.diagnostic import run_investigation
from app.api.persona import router as persona_router

api = FastAPI(
    title="KPI Intelligence Engine",
    description="Governed KPI Intelligence-to-Action Engine API",
    version="1.0.0"
)

# Include Persona Router for dynamic role + prompt narrative generation
api.include_router(persona_router, tags=["Persona Storytelling"])


@api.get("/health")
def health_check():
    return {"status": "healthy", "service": "kpi-engine"}


@api.post("/investigations")
def investigate(event: KPIMovementEvent):
    payload = run_investigation(event)
    return payload