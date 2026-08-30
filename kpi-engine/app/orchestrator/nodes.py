from app.agents.product import run_product_agent
from app.agents.customer import run_customer_agent
from app.agents.geography import run_geography_agent
from app.agents.channel import run_channel_agent

from app.analytics.contribution import calculate_contribution
from app.analytics.dependency import validate_dependency
from app.analytics.temporal import validate_temporal_precedence
from app.analytics.evidence import calculate_evidence_score
from app.analytics.contradictions import detect_contradictions

from app.orchestrator.llm import orchestrator_llm
from app.governance.engine import evaluate_recommendation
from app.schemas.diagnostic import DiagnosticPayload, Driver, Uncertainty, Recommendation


def product_node(state):
    finding = run_product_agent(state["movement"])
    return {"findings": [finding]}


def customer_node(state):
    finding = run_customer_agent(state["movement"])
    return {"findings": [finding]}


def geography_node(state):
    finding = run_geography_agent(state["movement"])
    return {"findings": [finding]}


def channel_node(state):
    finding = run_channel_agent(state["movement"])
    return {"findings": [finding]}


def analysis_node(state):
    results = []
    movement = state["movement"]
    findings = state.get("findings", [])

    for finding in findings:
        contrib = calculate_contribution(finding, movement)
        dep = validate_dependency(finding, movement.kpi_id)
        temp = validate_temporal_precedence(finding, movement)
        ev_score = calculate_evidence_score(finding)

        results.append({
            "agent": finding.agent_name,
            "claim": finding.claim,
            "driver_type": finding.driver_type,
            "dimension": finding.dimension,
            "contribution": contrib,
            "dependency": dep,
            "temporal": temp,
            "evidence_score": ev_score,
            "agent_confidence": finding.confidence,
        })

    return {"analytical_results": results}


def contradiction_node(state):
    findings = state.get("findings", [])
    contradictions = detect_contradictions(findings)
    return {"contradictions": contradictions}


def orchestrator_node(state):
    movement = state["movement"]
    findings = state.get("findings", [])
    analytical_results = state.get("analytical_results", [])
    contradictions = state.get("contradictions", [])

    prompt = f"""
You are the KPI Investigation Orchestrator.

KPI Movement:
{movement.model_dump_json()}

Agent Findings:
{[f.model_dump() for f in findings]}

Analytical Results:
{analytical_results}

Contradictions:
{contradictions}

Synthesize the validated findings into a formal DiagnosticPayload.
Rules:
1. Ground all numbers ONLY in the provided analytical results.
2. Link each driver to its supporting findings and computed contributions.
3. If contradictions exist or evidence is weak, flag uncertainty.
"""
    try:
        diagnostic = orchestrator_llm.invoke(prompt)
    except Exception:
        # Deterministic synthesis fallback
        drivers = []
        for i, res in enumerate(analytical_results):
            contrib = res.get("contribution", {})
            dep = res.get("dependency", {})
            temp = res.get("temporal", {})
            
            drivers.append(Driver(
                driver_id=f"DRV-{i+1:03d}",
                name=res.get("claim", "Unknown driver"),
                driver_type=res.get("driver_type", "unclassified"),
                contribution_absolute=contrib.get("absolute_contribution"),
                contribution_percentage=contrib.get("percentage_of_movement"),
                temporal_valid=temp.get("is_valid", True),
                dependency_valid=dep.get("is_valid", True),
                evidence_score=res.get("evidence_score", 0.5),
                diagnostic_confidence=res.get("agent_confidence", 0.7),
                supporting_findings=[res.get("agent", "agent")]
            ))

        recs = [
            Recommendation(
                lever_id="LEV-001",
                action=f"Investigate primary driver: {drivers[0].name if drivers else 'general movement'}",
                target=findings[0].dimension if findings else {},
                expected_impact={"mitigation_target": movement.absolute_change},
                owner_role="Operations Manager"
            )
        ]

        diagnostic = DiagnosticPayload(
            incident_id=movement.event_id,
            kpi_id=movement.kpi_id,
            observed_value=movement.observed_value,
            expected_value=movement.expected_value,
            percentage_change=movement.percentage_change,
            drivers=drivers,
            uncertainty=Uncertainty(
                status="LOW" if len(contradictions) == 0 else "HIGH",
                abstain=len(contradictions) > 0,
                reason="Contradictory findings detected across agent dimensions" if contradictions else None
            ),
            recommendations=recs,
            lineage=[{"source": "canonical_measurements", "timestamp": movement.analysis_end.isoformat()}]
        )

    return {"diagnostic_payload": diagnostic}


def governance_node(state):
    diagnostic = state.get("diagnostic_payload")
    if not diagnostic or not diagnostic.recommendations:
        return {"diagnostic_payload": diagnostic}

    for rec in diagnostic.recommendations:
        gov_input = {
            "action": rec.action,
            "driver": diagnostic.drivers[0].driver_type if diagnostic.drivers else "",
            "confidence": diagnostic.drivers[0].diagnostic_confidence if diagnostic.drivers else 0.8,
            "dataQualityStatus": "VALID"
        }
        gov_eval = evaluate_recommendation(gov_input)
        if isinstance(gov_eval, dict):
            # ZenEngine returns {"result": ...}
            raw_result = gov_eval.get("result", "AUTHORIZED")
            if isinstance(raw_result, dict):
                rec.decision_right = str(raw_result.get("result", "AUTHORIZED"))
            else:
                rec.decision_right = str(raw_result)
        else:
            rec.decision_right = "AUTHORIZED"

    return {"diagnostic_payload": diagnostic}
