from app.db.supabase import supabase


class RecommendationRepository:

    @staticmethod
    def get_recommendations(investigation_id: str):
        # First get driver candidates belonging to this investigation
        drivers_response = (
            supabase
            .table("driver_candidates")
            .select("id")
            .eq("investigation_id", investigation_id)
            .execute()
        )

        driver_ids = [driver["id"] for driver in drivers_response.data]

        if not driver_ids:
            return []

        # Then get recommendations associated with those drivers
        response = (
            supabase
            .table("recommendations")
            .select("*")
            .in_("driver_candidate_id", driver_ids)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_recommendation(recommendation_id: str):

        response = (
        supabase
        .table("recommendations")
        .select("*")
        .eq("id", recommendation_id)
        .maybe_single()
        .execute()
    )

        return response.data if response else None