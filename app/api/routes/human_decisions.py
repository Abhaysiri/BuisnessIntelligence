from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user

from app.services.human_decision_service import HumanDecisionService


router = APIRouter(
    prefix="/human-decisions",
    tags=["Human Decisions"]
)


class HumanDecisionRequest(BaseModel):
    decision: str
    comment: str | None = None
    correction_payload: dict | None = None


@router.post("/{recommendation_id}")
def make_human_decision(
    recommendation_id: str,
    request: HumanDecisionRequest,
    current_user: dict = Depends(get_current_user)
):

    try:

        return HumanDecisionService.make_decision(
            recommendation_id=recommendation_id,
            user_id=current_user["user_id"],
            decision=request.decision,
            comment=request.comment,
            correction_payload=request.correction_payload
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )