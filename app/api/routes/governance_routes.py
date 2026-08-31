from fastapi import APIRouter, HTTPException

from app.controllers.governance_controller import GovernanceController


router = APIRouter(
    prefix="/governance",
    tags=["Governance"]
)


# @router.post("/evaluate/{recommendation_id}")
# def evaluate_recommendation(
#     recommendation_id: str,
#     organization_id: str
# ):
#     result = GovernanceController.evaluate_recommendation(
#         recommendation_id,
#         organization_id
#     )

#     if not result:
#         raise HTTPException(
#             status_code=404,
#             detail="Recommendation not found"
#         )

#     return result


@router.get("/recommendation/{recommendation_id}")
def get_evaluations(recommendation_id: str):
    return GovernanceController.get_evaluations(
        recommendation_id
    )