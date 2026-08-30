def calculate_evidence_score(finding) -> float:
    score = 0.0

    # Has quantitative evidence?
    if finding.evidence:
        score += 0.4

    # Has timestamps?
    if any(e.timestamp is not None for e in finding.evidence):
        score += 0.2

    # Has direct metric values?
    if any(e.value is not None for e in finding.evidence):
        score += 0.2

    # Agent's own confidence contributes only partially.
    score += 0.2 * finding.confidence

    return min(score, 1.0)