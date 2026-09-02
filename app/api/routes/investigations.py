from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.services.investigation_service import InvestigationService


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"]
)


@router.get("/{investigation_id}")
def get_investigation(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    investigation = InvestigationService.get_investigation(
        investigation_id
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found"
        )

    return investigation


# POST /api/v1/investigations/ is redundant (KPI engine's /investigations is used instead)


@router.patch("/{investigation_id}/status")
def update_investigation_status(
    investigation_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    return InvestigationService.update_status(
        investigation_id,
        status
    )