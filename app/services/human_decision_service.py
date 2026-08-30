from app.db.supabase import supabase
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.human_decision_repository import HumanDecisionRepository


class HumanDecisionService:

    @staticmethod
    def make_decision(
        recommendation_id: str,
        user_id: str,
        decision: str,
        comment: str | None = None,
        correction_payload: dict | None = None
    ):

        valid_decisions = {
            "approve",
            "reject",
            "delegate",
            "request_changes"
        }

        if decision not in valid_decisions:
            raise ValueError(
                f"Invalid decision. Must be one of: {valid_decisions}"
            )

        # 1. Get recommendation
        recommendation = RecommendationRepository.get_recommendation(
            recommendation_id
        )

        if not recommendation:
            raise ValueError("Recommendation not found")

        old_status = recommendation["status"]

        # 2. Get organization_id
        diagnostic_payload_id = recommendation["diagnostic_payload_id"]

        diagnostic_response = (
            supabase
            .table("diagnostic_payloads")
            .select("investigation_id")
            .eq("id", diagnostic_payload_id)
            .maybe_single()
            .execute()
        )

        if not diagnostic_response or not diagnostic_response.data:
            raise ValueError("Diagnostic payload not found")

        investigation_id = diagnostic_response.data["investigation_id"]

        investigation_response = (
            supabase
            .table("investigations")
            .select("organization_id")
            .eq("id", investigation_id)
            .maybe_single()
            .execute()
        )

        if not investigation_response or not investigation_response.data:
            raise ValueError("Investigation not found")

        organization_id = investigation_response.data["organization_id"]

        # 3. Convert human decision → recommendation status
        status_map = {
            "approve": "approved",
            "reject": "rejected",
            "delegate": "delegated",
            "request_changes": "proposed"
        }

        new_status = status_map[decision]

        # 4. Update recommendation
        update_response = (
            supabase
            .table("recommendations")
            .update({
                "status": new_status
            })
            .eq("id", recommendation_id)
            .execute()
        )

        if not update_response.data:
            raise ValueError("Failed to update recommendation")

        # 5. Store human decision
        human_decision = HumanDecisionRepository.create_decision(
            recommendation_id=recommendation_id,
            user_id=user_id,
            decision=decision,
            comment=comment,
            correction_payload=correction_payload
        )

        if not human_decision:
            raise ValueError("Failed to store human decision")

        # 6. Create audit log
        audit_log = AuditRepository.create_audit_log(
            organization_id=organization_id,
            user_id=user_id,
            action=f"recommendation.{decision}",
            entity_type="recommendation",
            entity_id=recommendation_id,
            old_values={
                "status": old_status
            },
            new_values={
                "status": new_status
            }
        )

        # 7. Return result
        return {
            "recommendation": update_response.data[0],
            "human_decision": human_decision,
            "audit_log": audit_log
        }