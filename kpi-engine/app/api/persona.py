from fastapi import APIRouter

from app.schemas.persona import PersonaRequest
from app.orchestrator.persona import generate_persona_story
from app.services.diagnostic import get_diagnostic_payload


router = APIRouter()


@router.post("/persona/story")
def create_persona_story(
    payload_request: PersonaRequest,
    diagnostic_payload_id: str,
):

    diagnostic = get_diagnostic_payload(
        diagnostic_payload_id
    )

    result = generate_persona_story(
        diagnostic_payload=diagnostic.model_dump(),
        role=payload_request.role.value,
        persona_prompt=payload_request.prompt,
    )

    return result