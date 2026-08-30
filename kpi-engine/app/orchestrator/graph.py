from langgraph.graph import StateGraph, START, END

from app.orchestrator.state import InvestigationState
from app.orchestrator.nodes import (
    product_node,
    customer_node,
    geography_node,
    channel_node,
    analysis_node,
    contradiction_node,
    orchestrator_node,
    governance_node
)


builder = StateGraph(InvestigationState)

# Add Agent Swarm Nodes
builder.add_node("product_agent", product_node)
builder.add_node("customer_agent", customer_node)
builder.add_node("geography_agent", geography_node)
builder.add_node("channel_agent", channel_node)

# Add Analytical, Orchestration & Governance Nodes
builder.add_node("analysis", analysis_node)
builder.add_node("contradictions", contradiction_node)
builder.add_node("orchestrator", orchestrator_node)
builder.add_node("governance", governance_node)

# Fan-out: START executes all 4 agents in parallel
builder.add_edge(START, "product_agent")
builder.add_edge(START, "customer_agent")
builder.add_edge(START, "geography_agent")
builder.add_edge(START, "channel_agent")

# Fan-in: All agents feed findings into the central analysis node
builder.add_edge("product_agent", "analysis")
builder.add_edge("customer_agent", "analysis")
builder.add_edge("geography_agent", "analysis")
builder.add_edge("channel_agent", "analysis")

# Downstream pipeline
builder.add_edge("analysis", "contradictions")
builder.add_edge("contradictions", "orchestrator")
builder.add_edge("orchestrator", "governance")
builder.add_edge("governance", END)

investigation_graph = builder.compile()
app = investigation_graph