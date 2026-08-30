from app.services.recommendation_service import RecommendationService


class RecommendationController:

    @staticmethod
    def get_recommendations(investigation_id: str):
        return RecommendationService.get_recommendations(investigation_id)

    @staticmethod
    def get_recommendation(recommendation_id: str):
        return RecommendationService.get_recommendation(recommendation_id)