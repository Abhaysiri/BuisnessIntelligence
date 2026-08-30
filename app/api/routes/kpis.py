from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user

from app.services.kpi_service import KPIService


router = APIRouter(
    prefix="/kpis",
    tags=["KPIs"]
)


@router.get("/")
def get_kpis(
    current_user: dict = Depends(get_current_user)
):
    return KPIService.get_kpis()


@router.get("/{kpi_id}")
def get_kpi(
    kpi_id: str,
    current_user: dict = Depends(get_current_user)
):

    kpi = KPIService.get_kpi(kpi_id)

    if not kpi:
        raise HTTPException(
            status_code=404,
            detail="KPI not found"
        )

    return kpi


@router.get("/{kpi_id}/versions")
def get_kpi_versions(
    kpi_id: str,
    current_user: dict = Depends(get_current_user)
):

    return KPIService.get_kpi_versions(kpi_id)


@router.get("/{kpi_id}/measurements")
def get_kpi_measurements(
    kpi_id: str,
    current_user: dict = Depends(get_current_user)
):

    return KPIService.get_kpi_measurements(kpi_id)