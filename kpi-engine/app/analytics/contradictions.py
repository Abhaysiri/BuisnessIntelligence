from app.schemas.findings import AgentFinding


def detect_contradictions(findings: list[AgentFinding]) -> list[dict]:
    """
    Scans across all agent findings for numerical conflicts, conflicting directional claims,
    or incompatible dimension attributions.
    """
    contradictions = []

    for i in range(len(findings)):
        for j in range(i + 1, len(findings)):
            a = findings[i]
            b = findings[j]

            # 1. Exact same dimension slice with materially different values
            if (
                a.dimension
                and a.dimension == b.dimension
                and a.observed_value is not None
                and b.observed_value is not None
            ):
                if abs(a.observed_value - b.observed_value) > 0.01:
                    contradictions.append({
                        "finding_a": a.agent_name,
                        "finding_b": b.agent_name,
                        "type": "value_conflict",
                        "reason": f"Conflicting values for dimension {a.dimension}: {a.observed_value} vs {b.observed_value}"
                    })

            # 2. Opposite direction claim for the same dimension
            if (
                a.dimension
                and a.dimension == b.dimension
                and a.percentage_change is not None
                and b.percentage_change is not None
            ):
                if (a.percentage_change > 0 and b.percentage_change < 0) or (a.percentage_change < 0 and b.percentage_change > 0):
                    contradictions.append({
                        "finding_a": a.agent_name,
                        "finding_b": b.agent_name,
                        "type": "directional_conflict",
                        "reason": f"Opposite directional claims for {a.dimension}"
                    })

    return contradictions