from app.db.supabase import supabase


class HumanDecisionRepository:

    @staticmethod
    def create_decision(
        recommendation_id: str,
        user_id: str,
        decision: str,
        comment: str | None = None,
        correction_payload: dict | None = None
    ):
        response = (
            supabase
            .table("human_decisions")
            .insert({
                "recommendation_id": recommendation_id,
                "user_id": user_id,
                "decision": decision,
                "comment": comment,
                "correction_payload": correction_payload
            })
            .execute()
        )

        return response.data[0] if response.data else None

    @staticmethod
    def get_decisions(recommendation_id: str):
        response = (
            supabase
            .table("human_decisions")
            .select("*")
            .eq("recommendation_id", recommendation_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data