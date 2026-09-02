from fastapi import APIRouter

from app.controllers.governance_controller import GovernanceController


router = APIRouter(
    prefix="/governance",
    tags=["Governance"]
)


# POST /api/v1/governance/evaluate/{recommendation_id} is redundant (KPI engine handles governance via zen-engine)


@router.get("/recommendation/{recommendation_id}")
def get_evaluations(recommendation_id: str):
    return GovernanceController.get_evaluations(
        recommendation_id
    )