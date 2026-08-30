def evaluate_governance(request):
    rule_type = request.get("rule_type")
    active = request.get("active", True)
    magnitude = request.get("magnitude")

    # Rule 1: inactive rule
    if not active:
        return {
            "decision": "REJECT",
            "reason": "Governance rule is inactive"
        }

    # Rule 2: approval
    if rule_type == "approval":
        return {
            "decision": "REQUIRES_APPROVAL",
            "reason": "Request requires human approval"
        }

    # Rule 3: magnitude
    if magnitude is not None:
        if magnitude > 100000:
            return {
                "decision": "REQUIRES_APPROVAL",
                "reason": "Magnitude exceeds allowed threshold"
            }

    # Default
    return {
        "decision": "APPROVED",
        "reason": "Request satisfies governance rules"
    }