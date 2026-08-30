from app.repositories.recommendation_repository import RecommendationRepository


class RecommendationService:

    @staticmethod
    def get_recommendations(investigation_id: str):
        return RecommendationRepository.get_recommendations(investigation_id)

    @staticmethod
    def get_recommendation(recommendation_id: str):
        return RecommendationRepository.get_recommendation(recommendation_id)