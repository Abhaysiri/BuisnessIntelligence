from app.repositories.governance_repository import GovernanceRepository
from app.repositories.recommendation_repository import RecommendationRepository


class GovernanceService:

    @staticmethod
    def evaluate_recommendation(
        recommendation_id: str,
        organization_id: str
    ):
        recommendation = (
            RecommendationRepository
            .get_recommendation(recommendation_id)
        )

        if not recommendation:
            return None
        if recommendation["status"] == "rejected":
            decision_payload = {
        "recommendation_id": recommendation_id,
        "rules_evaluated": 0,
        "recommendation_status": recommendation["status"],
        "decision": "rejected",
        "reason": "Recommendation has already been rejected"
    }

            return GovernanceRepository.create_evaluation(
        recommendation_id=recommendation_id,
        status="rejected",
        decision_payload=decision_payload
        )

        rules = GovernanceRepository.get_active_rules(
            organization_id
        )

        status = "approved"
        required_approver = None
        allowed_magnitude = None
        applied_constraints = []

        for rule in rules:

            # Approval rule
            if rule["rule_type"] == "approval":

                status = "escalation_required"

                required_approver = (
                    rule.get("configuration", {})
                    .get("approver")
                )

                applied_constraints.append({
                    "rule": rule.get("rule_key"),
                    "type": "approval"
                })

            # Magnitude rule
            elif rule["rule_type"] == "magnitude":

                max_magnitude = (
                    rule.get("configuration", {})
                    .get("max_magnitude")
                )

                if max_magnitude is not None:

                    allowed_magnitude = max_magnitude

                    applied_constraints.append({
                        "rule": rule.get("rule_key"),
                        "type": "magnitude",
                        "max_magnitude": max_magnitude
                    })

        decision_payload = {
            "recommendation_id": recommendation_id,
            "rules_evaluated": len(rules),
            "recommendation_status": recommendation["status"],
            "decision": status
        }

        return GovernanceRepository.create_evaluation(
            recommendation_id=recommendation_id,
            status=status,
            required_approver=required_approver,
            allowed_magnitude=allowed_magnitude,
            applied_constraints=applied_constraints,
            decision_payload=decision_payload
        )

    @staticmethod
    def get_evaluations(
        recommendation_id: str
    ):
        return GovernanceRepository.get_evaluations(
            recommendation_id
        )