from app.db.supabase import supabase


class InvestigationRepository:

    @staticmethod
    def create(movement_event_id: str, organization_id: str):
        response = (
        supabase
        .table("investigations")
        .insert({
            "movement_event_id": movement_event_id,
            "organization_id": organization_id,
            "status": "pending"
        })
        .execute()
    )

        return response.data

    @staticmethod
    def get_by_id(investigation_id: str):
        response = (
            supabase
            .table("investigations")
            .select("*")
            .eq("id", investigation_id)
            .single()
            .execute()
        )

        return response.data

    @staticmethod
    def update_status(investigation_id: str, status: str):
        response = (
            supabase
            .table("investigations")
            .update({
                "status": status
            })
            .eq("id", investigation_id)
            .execute()
        )

        return response.data