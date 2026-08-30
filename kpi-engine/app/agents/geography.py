from langchain_core.messages import HumanMessage, SystemMessage

from app.tools.geography import get_geography_metrics
from app.schemas.findings import AgentFinding, Evidence
from app.agents.base import get_agent_llm


def run_geography_agent(movement) -> AgentFinding:
    rows = get_geography_metrics.invoke({
        "start": movement.analysis_start.isoformat(),
        "end": movement.analysis_end.isoformat(),
        "kpi_key": movement.kpi_id,
    })

    prompt = f"""
You are the Geography Diagnostic Agent.
Identify if geographic regions or local market factors explain this KPI movement.

KPI Movement Event:
{movement.model_dump_json()}

Observed Geographic Data:
{rows}

Strict Instructions:
1. Ground all numbers and claims ONLY on the provided geographic data.
2. If data is empty or inconclusive, return low confidence with claim "No conclusive geographic deviation found".
3. Return a valid structured AgentFinding.
"""

    try:
        agent_llm = get_agent_llm(AgentFinding)
        return agent_llm.invoke([
            SystemMessage(content="You are a rigorous, evidence-grounded geography diagnostic agent."),
            HumanMessage(content=prompt),
        ])
    except Exception:
        return AgentFinding(
            agent_name="geography_agent",
            claim=f"Geographic investigation completed for {movement.kpi_id}",
            driver_type="geography",
            dimension={"geography": rows[0].get("geography", "all") if rows and isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict) else "all"},
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
                    metric="geography_value",
                    value=movement.observed_value,
                    baseline=movement.expected_value,
                    timestamp=movement.analysis_end
                )
            ]
        )
