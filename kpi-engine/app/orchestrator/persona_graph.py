from langgraph.graph import StateGraph, START, END


def persona_node(state):
    result = generate_persona_story(
        state["diagnostic_payload"],
        state["role"],
        state["persona_prompt"],
    )

    return {
        "persona_result": result
    }


def governance_node(state):
    result = evaluate_recommendation(
        state["persona_result"].recommendations
    )

    return {
        "governance_result": result
    }


builder = StateGraph(PersonaState)

builder.add_node("persona_story", persona_node)
builder.add_node("governance", governance_node)

builder.add_edge(START, "persona_story")
builder.add_edge("persona_story", "governance")
builder.add_edge("governance", END)

persona_graph = builder.compile()