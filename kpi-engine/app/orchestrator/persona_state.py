from typing import TypedDict

from app.schemas.persona import PersonaRole
from app.schemas.diagnostic import DiagnosticPayload


class PersonaState(TypedDict, total=False):
    diagnostic_payload: DiagnosticPayload

    role: PersonaRole
    persona_prompt: str

    persona_story: dict