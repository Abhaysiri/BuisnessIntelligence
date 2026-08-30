import os
from langchain_openai import ChatOpenAI
from app.schemas.diagnostic import DiagnosticPayload
from app.config import settings

api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")

orchestrator_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key
).with_structured_output(DiagnosticPayload)