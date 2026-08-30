from app.db.supabase import supabase


class GovernanceRepository:

    @staticmethod
    def get_active_rules(organization_id: str):
        response = (
            supabase
            .table("governance_rules")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("active", True)
            .execute()
        )

        return response.data

    @staticmethod
    def create_evaluation(
        recommendation_id: str,
        status: str,
        required_approver: str | None = None,
        allowed_magnitude: float | None = None,
        applied_constraints: list | None = None,
        decision_payload: dict | None = None,
    ):
        response = (
            supabase
            .table("governance_evaluations")
            .insert({
                "recommendation_id": recommendation_id,
                "status": status,
                "required_approver": required_approver,
                "allowed_magnitude": allowed_magnitude,
                "applied_constraints": applied_constraints or [],
                "decision_payload": decision_payload or {},
            })
            .execute()
        )

        return response.data[0] if response.data else None

    @staticmethod
    def get_evaluations(recommendation_id: str):
        response = (
            supabase
            .table("governance_evaluations")
            .select("*")
            .eq("recommendation_id", recommendation_id)
            .order("evaluated_at", desc=True)
            .execute()
        )

        return response.data