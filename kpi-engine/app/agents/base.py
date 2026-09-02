from app.llm_client import get_gemini_structured_llm


def get_agent_llm(structured_schema):
    """
    Returns an LLM instance configured with structured output.
    """
    return get_gemini_structured_llm(structured_schema, temperature=0.0)