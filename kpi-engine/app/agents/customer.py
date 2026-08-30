from langchain_core.messages import HumanMessage, SystemMessage

from app.tools.customer import get_customer_segment_metrics
from app.schemas.findings import AgentFinding, Evidence
from app.agents.base import get_agent_llm


def run_customer_agent(movement) -> AgentFinding:
    rows = get_customer_segment_metrics.invoke({
        "start": movement.analysis_start.isoformat(),
        "end": movement.analysis_end.isoformat(),
        "kpi_key": movement.kpi_id,
    })

    prompt = f"""
You are the Customer Segment & Device Diagnostic Agent.
Identify if customer cohorts, tier shifts, or device OS issues explain this KPI movement.

KPI Movement Event:
{movement.model_dump_json()}

Observed Customer Segment & Device Data:
{rows}

Strict Instructions:
1. Ground all numbers and claims ONLY on the provided customer data.
2. If data is empty or inconclusive, return low confidence with claim "No conclusive customer segment deviation found".
3. Return a valid structured AgentFinding.
"""

    try:
        agent_llm = get_agent_llm(AgentFinding)
        return agent_llm.invoke([
            SystemMessage(content="You are a rigorous, evidence-grounded customer segment diagnostic agent."),
            HumanMessage(content=prompt),
        ])
    except Exception:
        return AgentFinding(
            agent_name="customer_agent",
            claim=f"Customer segment investigation completed for {movement.kpi_id}",
            driver_type="customer_segment",
            dimension={"customer_segment": rows[0].get("customer_segment", "all") if rows and isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict) else "all"},
            observed_value=movement.observed_value,
            baseline_value=movement.expected_value,
            absolute_change=movement.absolute_change,
            percentage_change=movement.percentage_change,
            time_start=movement.analysis_start,
            time_end=movement.analysis_end,
            confidence=0.80 if rows and "error" not in rows[0] else 0.5,
            evidence=[
                Evidence(
                    source_id="canonical_measurements",
                    source_type="database",
                    metric="customer_segment_value",
                    value=movement.observed_value,
                    baseline=movement.expected_value,
                    timestamp=movement.analysis_end
                )
            ]
        )
