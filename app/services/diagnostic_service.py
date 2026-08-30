from app.repositories.diagnostic_repository import DiagnosticRepository


class DiagnosticService:

    @staticmethod
    def get_findings(investigation_id: str):
        return DiagnosticRepository.get_findings(investigation_id)

    @staticmethod
    def get_evidence(investigation_id: str):
        return DiagnosticRepository.get_evidence(investigation_id)

    @staticmethod
    def get_driver_candidates(investigation_id: str):
        return DiagnosticRepository.get_driver_candidates(investigation_id)