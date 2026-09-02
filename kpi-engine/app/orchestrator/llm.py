from app.schemas.diagnostic import DiagnosticPayload
from app.llm_client import get_gemini_structured_llm

orchestrator_llm = get_gemini_structured_llm(DiagnosticPayload, temperature=0.0)