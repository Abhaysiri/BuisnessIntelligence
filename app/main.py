from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.kpis import router as kpi_router
from app.api.routes.agents import router as agent_router
from app.api.routes.investigations import router as investigation_router
from app.api.routes.diagnostics import router as diagnostic_router
from app.api.routes.recommendations import router as recommendation_router
from app.api.routes.governance_routes import router as governance_router
from app.api.routes.human_decisions import router as human_decision_router
from app.api.routes.storage import router as storage_router
from app.api.routes.audit import router as audit_router


app = FastAPI(title="Business Intelligence Backend")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    kpi_router,
    prefix="/api/v1"
)

app.include_router(
    agent_router,
    prefix="/api/v1"
)

app.include_router(
    investigation_router,
    prefix="/api/v1"
)

app.include_router(
    diagnostic_router,
    prefix="/api/v1"
)

app.include_router(
    recommendation_router,
    prefix="/api/v1"
)

app.include_router(
    governance_router,
    prefix="/api/v1"
)

app.include_router(
    human_decision_router,
    prefix="/api/v1"
)

app.include_router(
    storage_router,
    prefix="/api/v1"
)

app.include_router(
    audit_router,
    prefix="/api/v1"
)


@app.get("/")
def root():
    return {
        "message": "Business Intelligence Backend",
        "status": "online",
        "version": "2.0.0"
    }