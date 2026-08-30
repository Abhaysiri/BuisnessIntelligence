from app.services.governance_service import GovernanceService


class GovernanceController:

    @staticmethod
    def evaluate_recommendation(
        recommendation_id: str,
        organization_id: str
    ):
        return GovernanceService.evaluate_recommendation(
            recommendation_id,
            organization_id
        )

    @staticmethod
    def get_evaluations(
        recommendation_id: str
    ):
        return GovernanceService.get_evaluations(
            recommendation_id
        )