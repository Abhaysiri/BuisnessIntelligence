from app.repositories.audit_repository import AuditRepository


class AuditService:

    @staticmethod
    def log_action(
        organization_id: str,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        trace_id: str | None = None
    ):
        return AuditRepository.create_audit_log(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            trace_id=trace_id
        )

    @staticmethod
    def get_entity_logs(entity_type: str, entity_id: str):

        return AuditRepository.get_entity_logs(
            entity_type,
            entity_id
        )