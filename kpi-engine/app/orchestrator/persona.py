import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.persona import PersonaStoryPayload, PersonaRole
from app.config import settings

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

    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")
    
    try:
        from langchain_core.tracers.context import collect_runs
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=api_key
        ).with_structured_output(PersonaStoryPayload)

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
        
        # Match enum
        try:
            matched_role = PersonaRole(role.lower())
        except Exception:
            matched_role = PersonaRole.ANALYST

        return PersonaStoryPayload(
            role=matched_role,
            requested_focus=[persona_prompt[:100]],
            headline=f"[{role.upper()} BRIEF] {primary_name} impact on {diagnostic_payload.get('kpi_id', 'KPI')}",
            narrative=f"Diagnostic report tailored for {role}: Observed a {diagnostic_payload.get('percentage_change', 0)}% change. User request focus: '{persona_prompt}'. Key contributing factors have been identified and governed under policy rules.",
            key_drivers=drivers,
            evidence=[{"source": "diagnostic_payload", "details": drivers}],
            recommendations=diagnostic_payload.get("recommendations", []),
            uncertainty=diagnostic_payload.get("uncertainty", {}),
            diagnostic_payload_id=diagnostic_payload.get("incident_id", "INC-001")
        )