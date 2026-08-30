from app.db.supabase import supabase


class AuditRepository:

    @staticmethod
    def create_audit_log(
        organization_id: str,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        trace_id: str | None = None
    ):
        response = (
            supabase
            .table("audit_logs")
            .insert({
                "organization_id": organization_id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "old_values": old_values,
                "new_values": new_values,
                "trace_id": trace_id
            })
            .execute()
        )

        return response.data[0] if response.data else None

    @staticmethod
    def get_entity_logs(entity_type: str, entity_id: str):
        response = (
            supabase
            .table("audit_logs")
            .select("*")
            .eq("entity_type", entity_type)
            .eq("entity_id", entity_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data