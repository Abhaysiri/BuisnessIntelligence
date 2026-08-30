from app.repositories.agent_repository import AgentRepository


class AgentService:

    @staticmethod
    def get_agents():
        return AgentRepository.get_all()

    @staticmethod
    def get_runs(investigation_id: str):
        return AgentRepository.get_runs(investigation_id)

    @staticmethod
    def get_findings(agent_run_id: str):
        return AgentRepository.get_findings(agent_run_id)

    @staticmethod
    def get_evidence(finding_id: str):
        return AgentRepository.get_evidence(finding_id)

    @staticmethod
    def get_driver_candidates(investigation_id: str):
        return AgentRepository.get_driver_candidates(investigation_id)