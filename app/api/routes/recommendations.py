from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user

from app.controllers.recommendation_controller import (
    RecommendationController
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/investigation/{investigation_id}")
def get_recommendations(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):

    recommendations = (
        RecommendationController.get_recommendations(
            investigation_id
        )
    )

    return {
        "investigation_id": investigation_id,
        "count": len(recommendations),
        "recommendations": recommendations
    }


@router.get("/{recommendation_id}")
def get_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_current_user)
):

    recommendation = (
        RecommendationController.get_recommendation(
            recommendation_id
        )
    )

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    return recommendation