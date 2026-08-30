from app.db.supabase import supabase


class AgentRepository:

    @staticmethod
    def get_all():
        response = (
            supabase
            .table("agent_definitions")
            .select("*")
            .eq("active", True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_runs(investigation_id: str):
        response = (
            supabase
            .table("agent_runs")
            .select("*")
            .eq("investigation_id", investigation_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data


    @staticmethod
    def get_findings(agent_run_id: str):
        response = (
            supabase
            .table("agent_findings")
            .select("*")
            .eq("agent_run_id", agent_run_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_evidence(finding_id: str):
        response = (
            supabase
            .table("finding_evidence")
            .select("*")
            .eq("finding_id", finding_id)
            .order("evidence_timestamp", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def get_driver_candidates(investigation_id: str):
        response = (
            supabase
            .table("driver_candidates")
            .select("*")
            .eq("investigation_id", investigation_id)
            .order("rank")
            .execute()
        )

        return response.data