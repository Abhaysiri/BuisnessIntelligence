from app.db.supabase import supabase


class KPIRepository:

    @staticmethod
    def get_all():
        response = (
            supabase
            .table("kpi_definitions")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_by_id(kpi_id: str):
        response = (
            supabase
            .table("kpi_definitions")
            .select("*")
            .eq("id", kpi_id)
            .single()
            .execute()
        )

        return response.data

    @staticmethod
    def get_versions(kpi_id: str):
        response = (
            supabase
            .table("kpi_versions")
            .select("*")
            .eq("kpi_id", kpi_id)
            .order("version", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_measurements(kpi_id: str):
        response = (
            supabase
            .table("canonical_measurements")
            .select("*")
            .eq("kpi_id", kpi_id)
            .order("observed_at", desc=True)
            .execute()
        )

        return response.data