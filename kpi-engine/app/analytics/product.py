from app.analytics.contribution import calculate_contribution
from app.analytics.dependency import validate_dependency
from app.analytics.temporal import validate_temporal_precedence
from app.analytics.evidence import calculate_evidence_score


def analyze_product_finding(finding, movement):
    return {
        "agent": finding.agent_name,
        "claim": finding.claim,
        "driver_type": finding.driver_type,
        "dimension": finding.dimension,
        "contribution": calculate_contribution(finding, movement),
        "dependency": validate_dependency(finding, movement.kpi_id),
        "temporal": validate_temporal_precedence(finding, movement),
        "evidence_score": calculate_evidence_score(finding),
        "confidence": finding.confidence,
    }