def evaluate_governance(request):
    rule_type = request.get("rule_type")
    active = request.get("active", True)
    magnitude = request.get("magnitude")
    user_role = request.get("user_role")
    domain = request.get("domain")
    action = request.get("action")
    discount = request.get("discount")
    ad_spend_increase = request.get("ad_spend_increase")

    # Rule 1: inactive rule
    if not active:
        return {
            "decision": "REJECT",
            "reason": "Governance rule is inactive"
        }

    # Rule: Role-level checks if provided
    if user_role:
        is_vp = "vp" in user_role.lower() or "cro" in user_role.lower() or "cfo" in user_role.lower()
        is_lead = "lead" in user_role.lower()
        can_write = is_vp or is_lead

        # Write actions require VP or Lead
        if action and action != "request_kpi_story" and not can_write:
            return {
                "decision": "REQUIRES_APPROVAL",
                "required_approver": "VP or Lead in " + (domain or "domain"),
                "reason": f"Role '{user_role}' has Read-only permissions. Action requires VP/Lead authority."
            }

        # Discount threshold rules
        if discount is not None:
            if discount > 20 and not is_vp:
                return {
                    "decision": "REQUIRES_APPROVAL",
                    "required_approver": "VP of Sales / CRO",
                    "reason": "Discounts exceeding 20% require VP of Global Sales authorization"
                }
            elif discount > 10 and not (is_vp or is_lead):
                return {
                    "decision": "REQUIRES_APPROVAL",
                    "required_approver": "Lead / Sales Manager",
                    "reason": "Discounts exceeding 10% require Lead authorization"
                }

        # Ad spend increase threshold rules
        if ad_spend_increase is not None:
            if ad_spend_increase > 1000 and not is_vp:
                return {
                    "decision": "REQUIRES_APPROVAL",
                    "required_approver": "VP of Marketing",
                    "reason": "Ad spend increases exceeding $1,000/day require VP approval"
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