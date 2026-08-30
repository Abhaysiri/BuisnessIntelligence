import os
from langchain_openai import ChatOpenAI
from app.config import settings


def get_agent_llm(structured_schema):
    """
    Returns an LLM instance configured with structured output.
    """
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )
    return llm.with_structured_output(structured_schema)