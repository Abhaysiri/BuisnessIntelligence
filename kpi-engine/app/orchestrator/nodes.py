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


from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def product_node(state):
    with tracer.start_as_current_span("product_node") as span:
        finding = run_product_agent(state["movement"])
        span.set_attribute("agent.finding_confidence", finding.confidence if finding else 0.0)
        return {"findings": [finding]}


def customer_node(state):
    with tracer.start_as_current_span("customer_node") as span:
        finding = run_customer_agent(state["movement"])
        span.set_attribute("agent.finding_confidence", finding.confidence if finding else 0.0)
        return {"findings": [finding]}


def geography_node(state):
    with tracer.start_as_current_span("geography_node") as span:
        finding = run_geography_agent(state["movement"])
        span.set_attribute("agent.finding_confidence", finding.confidence if finding else 0.0)
        return {"findings": [finding]}


def channel_node(state):
    with tracer.start_as_current_span("channel_node") as span:
        finding = run_channel_agent(state["movement"])
        span.set_attribute("agent.finding_confidence", finding.confidence if finding else 0.0)
        return {"findings": [finding]}


def analysis_node(state):
    with tracer.start_as_current_span("analysis_node") as span:
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
        
        span.set_attribute("analysis.result_count", len(results))
        return {"analytical_results": results}


def contradiction_node(state):
    with tracer.start_as_current_span("contradiction_node") as span:
        findings = state.get("findings", [])
        contradictions = detect_contradictions(findings)
        span.set_attribute("analysis.contradiction_count", len(contradictions))
        return {"contradictions": contradictions}


def orchestrator_node(state):
    with tracer.start_as_current_span("orchestrator_node") as span:
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
        span.set_attribute("llm.prompt", prompt)
        try:
            diagnostic = orchestrator_llm.invoke(prompt)
            span.set_attribute("llm.response", diagnostic.model_dump_json() if diagnostic else "")
        except Exception as e:
            print(f"Orchestrator LLM failed: {e}")
            
            # Record OpenTelemetry error span
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Return an explicit failure state rather than swallowing
            diagnostic = DiagnosticPayload(
                incident_id=movement.event_id,
                kpi_id=movement.kpi_id,
                observed_value=movement.observed_value,
                expected_value=movement.expected_value,
                percentage_change=movement.percentage_change,
                drivers=[],
                uncertainty=Uncertainty(
                    status="HIGH",
                    abstain=True,
                    reason=f"LLM Orchestrator failed to synthesize: {e}"
                ),
                recommendations=[],
                lineage=[{"source": "error_fallback", "timestamp": movement.analysis_end.isoformat()}]
            )

        return {"diagnostic_payload": diagnostic}


def governance_node(state):
    with tracer.start_as_current_span("governance_node") as span:
        diagnostic = state.get("diagnostic_payload")
        if not diagnostic or not diagnostic.recommendations:
            return {"diagnostic_payload": diagnostic}

        # Extract dynamic DQ score from state
        dq_score = state.get("dq_score", 1.0)
        span.set_attribute("governance.dq_score", dq_score)
        
        # Map DQ Score (0.0 to 1.0) to Data Quality Status strings used by GoRules
        if dq_score >= 0.90:
            dq_status = "VALID"
        elif dq_score >= 0.70:
            dq_status = "DEGRADED"
        else:
            dq_status = "INVALID"
        
        span.set_attribute("governance.dq_status", dq_status)

        for rec in diagnostic.recommendations:
            gov_input = {
                "action": rec.action,
                "driver": diagnostic.drivers[0].driver_type if diagnostic.drivers else "",
                "confidence": diagnostic.drivers[0].diagnostic_confidence if diagnostic.drivers else 0.8,
                "dataQualityStatus": dq_status
            }
            try:
                gov_eval = evaluate_recommendation(gov_input)
                if isinstance(gov_eval, dict):
                    # ZenEngine returns {"result": ...}
                    raw_result = gov_eval.get("result", "REQUIRES_HUMAN_REVIEW")
                    if isinstance(raw_result, dict):
                        rec.decision_right = str(raw_result.get("result", "REQUIRES_HUMAN_REVIEW"))
                    else:
                        rec.decision_right = str(raw_result)
                else:
                    rec.decision_right = "REQUIRES_HUMAN_REVIEW"
                span.set_attribute(f"governance.decision.{rec.action}", rec.decision_right)
            except Exception as e:
                print(f"Governance rule evaluation failed: {e}")
                rec.decision_right = "REQUIRES_HUMAN_REVIEW"
                from opentelemetry.trace.status import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.set_attribute(f"governance.decision.{rec.action}", rec.decision_right)

        return {"diagnostic_payload": diagnostic}
