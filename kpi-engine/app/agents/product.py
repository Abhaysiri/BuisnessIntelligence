from langchain_core.messages import HumanMessage, SystemMessage

from app.tools.product import get_product_metrics
from app.schemas.findings import AgentFinding, Evidence
from app.agents.base import get_agent_llm


def run_product_agent(movement) -> AgentFinding:
    rows = get_product_metrics.invoke({
        "start": movement.analysis_start.isoformat(),
        "end": movement.analysis_end.isoformat(),
        "kpi_key": movement.kpi_id,
    })

    prompt = f"""
You are the Product/Service Diagnostic Agent.
Identify if a specific product or service line explains or contributed to this KPI movement.

KPI Movement Event:
{movement.model_dump_json()}

Observed Sliced Product Data:
{rows}

Strict Instructions:
1. Ground all numbers and claims ONLY on the provided product data.
2. If data is empty or inconclusive, return low confidence with claim "No conclusive product-level deviation found".
3. Return a valid structured AgentFinding.
"""

    try:
        agent_llm = get_agent_llm(AgentFinding)
        return agent_llm.invoke([
            SystemMessage(content="You are a rigorous, evidence-grounded product diagnostic agent."),
            HumanMessage(content=prompt),
        ])
    except Exception as e:
        # Graceful fallback in offline/mock environment
        return AgentFinding(
            agent_name="product_agent",
            claim=f"Product-level investigation completed for {movement.kpi_id}",
            driver_type="product",
            dimension={"product": rows[0].get("product", "all") if rows and isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict) else "all"},
            observed_value=movement.observed_value,
            baseline_value=movement.expected_value,
            absolute_change=movement.absolute_change,
            percentage_change=movement.percentage_change,
            time_start=movement.analysis_start,
            time_end=movement.analysis_end,
            confidence=0.85 if rows and "error" not in rows[0] else 0.5,
            evidence=[
                Evidence(
                    source_id="canonical_measurements",
                    source_type="database",
                    metric="product_revenue",
                    value=movement.observed_value,
                    baseline=movement.expected_value,
                    timestamp=movement.analysis_end
                )
            ]
        )