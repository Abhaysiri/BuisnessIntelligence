from app.repositories.investigation_repository import InvestigationRepository


class InvestigationService:

    @staticmethod
    def create_investigation(
        movement_event_id: str,
        organization_id: str
    ):
        return InvestigationRepository.create(
            movement_event_id,
            organization_id
        )

    @staticmethod
    def get_investigation(investigation_id: str):
        return InvestigationRepository.get_by_id(investigation_id)

    @staticmethod
    def update_status(
        investigation_id: str,
        status: str
    ):
        return InvestigationRepository.update_status(
            investigation_id,
            status
        )