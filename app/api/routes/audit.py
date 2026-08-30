from fastapi import APIRouter

from app.services.audit_service import AuditService


router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)


@router.get("/{entity_type}/{entity_id}")
def get_audit_logs(
    entity_type: str,
    entity_id: str
):
    return AuditService.get_entity_logs(
        entity_type,
        entity_id
    )