import os
import time
from langsmith import traceable
from app.monitoring.tracing import get_tracing_context
from app.monitoring.feedback import FeedbackRequest, submit_feedback

# --- Mock Components ---

@traceable(name="1_Router")
def router(kpi_movement):
    # Determines which agents to call
    return ["sales_agent", "marketing_agent"]

@traceable(name="2_SalesAgent")
def sales_agent(kpi_movement):
    # Mock tool call inside agent
    retrieve_sales_data(kpi_movement)
    return {"sales_driver": "Discounting"}

@traceable(name="Tool_RetrieveSalesData")
def retrieve_sales_data(kpi_movement):
    # E.g., Pinecone or Database retrieval
    time.sleep(0.1)
    return "Data from db"

@traceable(name="3_Analytics")
def analytics(agent_outputs):
    # Perform deterministic calculations
    return {"calculated_impact": 15.2}

@traceable(name="4_Contradictions")
def check_contradictions(analytics_output, agent_outputs):
    # e.g., sales says discounting increased volume, marketing says volume dropped
    return False

@traceable(name="5_Orchestrator")
def orchestrator(kpi_movement):
    routes = router(kpi_movement)
    agent_outputs = []
    if "sales_agent" in routes:
        agent_outputs.append(sales_agent(kpi_movement))
    
    analytics_out = analytics(agent_outputs)
    has_contradiction = check_contradictions(analytics_out, agent_outputs)
    
    diagnostic_payload = {
        "kpi_movement": kpi_movement,
        "drivers": agent_outputs,
        "impact": analytics_out,
        "has_contradiction": has_contradiction
    }
    return diagnostic_payload

@traceable(name="6_GoRules")
def call_gorules(diagnostic_payload):
    # Send to GoRules engine, return Payload2
    return {"policy_action": "alert_vp", **diagnostic_payload}

@traceable(name="7_PersonaStorytelling")
def generate_persona_story(payload2):
    # Use LLM to generate the final story
    return f"Story for VP: KPI {payload2['kpi_movement']} dropped due to {payload2['drivers']}."

# --- Main Entry Point (Root Trace) ---
from langsmith.run_helpers import get_current_run_tree

@traceable(name="InvestigationRoot")
def investigate_kpi_movement(kpi_movement: str):
    """
    This is the root trace for a single investigation.
    Everything called within this function will be nested under this root run.
    """
    diagnostic_payload = orchestrator(kpi_movement)
    payload2 = call_gorules(diagnostic_payload)
    final_story = generate_persona_story(payload2)
    
    # Capture current run ID for our example
    run_tree = get_current_run_tree()
    run_id = str(run_tree.id) if run_tree else "00000000-0000-0000-0000-000000000000"
    
    return {
        "diagnostic_payload": diagnostic_payload,
        "final_story": final_story,
        "run_id": run_id
    }

def run_example():
    """
    Demonstrates the complete lifecycle:
    1. Runtime execution with nested tracing
    2. Simulated Human Feedback linking to the trace
    """
    print("--- 1. Executing KPI Investigation ---")
    
    run_id = "00000000-0000-0000-0000-000000000000"
    
    # Use tracing context to ensure LangSmith captures it
    with get_tracing_context():
        result = investigate_kpi_movement("Revenue Drop Q3")
        print("Investigation Result:", result["final_story"])
        run_id = result.get("run_id", run_id)
        
    # Give LangSmith a moment to ingest the background trace before sending feedback
    time.sleep(2)
        
    print(f"\n--- 2. Simulating Human Feedback for run {run_id} ---")
    
    feedback = FeedbackRequest(
        trace_id=run_id,
        reviewer_role="VP_Sales",
        verdict=0, # Bad verdict
        error_category="evidence_grounding_failure",
        correction={"final_story": "Corrected story: It was actually seasonality."},
        comments="The agent missed the seasonality factor."
    )
    
    print("Submitting feedback and adding to evaluation dataset for next CI/CD cycle...")
    submit_feedback(feedback)
    print("Feedback submission complete.")

if __name__ == "__main__":
    run_example()
