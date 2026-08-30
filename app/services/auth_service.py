from app.db.supabase import supabase


class AuthService:

    @staticmethod
    def get_user_context(user_id: str):

        profile_response = (
            supabase
            .table("profiles")
            .select("user_id, full_name, email")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        if not profile_response or not profile_response.data:
            raise ValueError("User profile not found")

        membership_response = (
            supabase
            .table("organization_members")
            .select(
                "organization_id, role"
            )
            .eq("user_id", user_id)
            .execute()
        )

        memberships = membership_response.data or []

        return {
            "user_id": user_id,
            "profile": profile_response.data,
            "organizations": memberships
        }