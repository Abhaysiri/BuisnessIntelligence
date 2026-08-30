from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user

from app.services.diagnostic_service import DiagnosticService


router = APIRouter(
    prefix="/diagnostics",
    tags=["Diagnostics"]
)


@router.get("/{investigation_id}/findings")
def get_findings(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return DiagnosticService.get_findings(investigation_id)


@router.get("/{investigation_id}/evidence")
def get_evidence(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return DiagnosticService.get_evidence(investigation_id)


@router.get("/{investigation_id}/drivers")
def get_driver_candidates(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return DiagnosticService.get_driver_candidates(
        investigation_id
    )