import os
import sys
from datetime import datetime, timezone

# Ensure project path is accessible
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.schemas.movement import KPIMovementEvent
from app.schemas.persona import PersonaRequest, PersonaRole
from app.services.diagnostic import run_investigation, get_diagnostic_payload
from app.orchestrator.persona import generate_persona_story


def test_e2e_investigation():
    print("==================================================")
    print("1. Creating Synthetic KPI Movement Event")
    print("==================================================")
    
    event = KPIMovementEvent(
        event_id="INC-2026-001",
        kpi_id="monthly_revenue",
        analysis_start=datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
        analysis_end=datetime(2026, 5, 31, 23, 59, 59, tzinfo=timezone.utc),
        observed_value=70000.0,
        expected_value=100000.0,
        absolute_change=-30000.0,
        percentage_change=-30.0,
        statistical_score=3.45,
        materiality_status="MATERIAL",
        dimensions=["product", "customer_segment", "geography", "sales_channel"]
    )
    print(f"Event: {event.event_id} | KPI: {event.kpi_id} | Drop: {event.percentage_change}% (${event.absolute_change})")

    print("\n==================================================")
    print("2. Invoking Parallel LangGraph Swarm & Analytics")
    print("==================================================")
    payload = run_investigation(event)

    print(f"Incident ID: {payload.incident_id}")
    print(f"KPI: {payload.kpi_id} | Observed: ${payload.observed_value} vs Expected: ${payload.expected_value}")
    print(f"Uncertainty Status: {payload.uncertainty.status} (Abstain: {payload.uncertainty.abstain})")
    
    print("\n--- Drivers Identified ---")
    for d in payload.drivers:
        print(f"  - [{d.driver_id}] {d.name}")
        print(f"      Type: {d.driver_type} | Abs Contrib: {d.contribution_absolute} | % Contrib: {d.contribution_percentage}%")
        print(f"      Temporal Valid: {d.temporal_valid} | Dependency Valid: {d.dependency_valid} | Ev Score: {d.evidence_score}")

    print("\n--- Governed Recommendations ---")
    for r in payload.recommendations:
        print(f"  - [{r.lever_id}] {r.action} -> Decision Right: {r.decision_right} (Owner: {r.owner_role})")

    print("\n==================================================")
    print("3. Testing Dynamic Persona Storytelling (Engineering)")
    print("==================================================")
    eng_request = PersonaRequest(
        role=PersonaRole.ENGINEERING,
        prompt="Explain technical system latency, checkout errors, and service dependencies affecting this incident."
    )
    eng_story = generate_persona_story(
        diagnostic_payload=payload.model_dump(),
        role=eng_request.role.value,
        persona_prompt=eng_request.prompt
    )
    print(f"Headline: {eng_story.headline}")
    print(f"Narrative: {eng_story.narrative}")

    print("\n==================================================")
    print("4. Testing Dynamic Persona Storytelling (Executive)")
    print("==================================================")
    exec_request = PersonaRequest(
        role=PersonaRole.EXECUTIVE,
        prompt="Provide a high-level summary of financial revenue loss, top impacted segments, and recommended next steps."
    )
    exec_story = generate_persona_story(
        diagnostic_payload=payload.model_dump(),
        role=exec_request.role.value,
        persona_prompt=exec_request.prompt
    )
    print(f"Headline: {exec_story.headline}")
    print(f"Narrative: {exec_story.narrative}")
    print("\n[SUCCESS] End-to-End Test Completed Successfully!")


if __name__ == "__main__":
    test_e2e_investigation()
