from app.schemas.findings import AgentFinding
from app.schemas.movement import KPIMovementEvent


def validate_temporal_precedence(finding: AgentFinding, movement: KPIMovementEvent) -> dict:
    """
    Verifies that the evidence and finding time windows align with or precede
    the KPI movement event period (A precedes or coincides with B).
    """
    # Check finding-level window
    if finding.time_end and movement.analysis_start:
        if finding.time_end < movement.analysis_start:
            # Finding ended before the movement started - could be a preceding leading indicator
            pass

    invalid_evidence = []
    for ev in finding.evidence:
        if ev.timestamp:
            # If evidence occurred strictly after the analysis end window, it cannot explain the event
            if movement.analysis_end and ev.timestamp > movement.analysis_end:
                invalid_evidence.append({
                    "source_id": ev.source_id,
                    "timestamp": ev.timestamp.isoformat(),
                    "reason": "Timestamp occurs after movement analysis window"
                })

    is_valid = len(invalid_evidence) == 0

    return {
        "status": "VALID" if is_valid else "INVALID_PRECEDENCE",
        "is_valid": is_valid,
        "invalid_evidence": invalid_evidence
    }
