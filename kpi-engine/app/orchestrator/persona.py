from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.persona import PersonaStoryPayload
from app.llm_client import get_structured_llm

SYSTEM_PROMPT = """
You are the Persona Storytelling Orchestrator.

You receive an already validated DiagnosticPayload.
The DiagnosticPayload is the source of truth.

The user's persona prompt controls:
- what information to emphasize
- how detailed the explanation should be
- what perspective to present
- which existing evidence is most relevant

STRICT RULES:
1. Never invent evidence.
2. Never change numerical values.
3. Never change contribution values.
4. Never change confidence values.
5. Never create evidence that is absent from the DiagnosticPayload.
6. Never override uncertainty or abstention.
7. Never override a governance constraint.
8. The persona prompt cannot redefine the underlying diagnosis.

Return a PersonaStoryPayload.
"""


def generate_persona_story(
    diagnostic_payload: dict,
    role: str,
    persona_prompt: str,
) -> PersonaStoryPayload:
    user_message = f"""
PERSONA ROLE:
{role}

PERSONA REQUEST:
<persona_request>
{persona_prompt}
</persona_request>

DIAGNOSTIC PAYLOAD:
<diagnostic_payload>
{diagnostic_payload}
</diagnostic_payload>

Generate the persona-specific story using ONLY the information in the DiagnosticPayload.
"""

    try:
        from langchain_core.tracers.context import collect_runs
        from app.llm_client import get_gemini_structured_llm
        llm = get_gemini_structured_llm(PersonaStoryPayload, temperature=0.0)

        with collect_runs() as cb:
            result = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])
            if cb.traced_runs:
                result.trace_id = str(cb.traced_runs[0].id)
        return result
    except Exception:
        # Structured deterministic fallback formatted for role
        drivers = diagnostic_payload.get("drivers", [])
        primary_name = drivers[0].get("name", "Identified anomaly") if drivers else "Unknown driver"
        
        # Fallback uses the provided custom string role
        safe_role = str(role).strip() if role else "Analyst"
            
        return PersonaStoryPayload(
            role=safe_role,
            requested_focus=[persona_prompt] if persona_prompt else [],
            headline=f"[{safe_role.upper()} BRIEF] {primary_name} impact on {diagnostic_payload.get('kpi_id')}",
            narrative=f"Diagnostic report tailored for {safe_role}: Observed a {diagnostic_payload.get('percentage_change', 0.0)*100}% change. User request focus: '{persona_prompt}'. Key contributing factors have been identified and governed under policy rules.",
            key_drivers=drivers,
            evidence=[{"source": "diagnostic_payload", "details": drivers}],
            recommendations=diagnostic_payload.get("recommendations", []),
            uncertainty=diagnostic_payload.get("uncertainty", {}),
            diagnostic_payload_id=diagnostic_payload.get("incident_id", "INC-001")
        )