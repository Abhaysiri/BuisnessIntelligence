from app.services.diagnostic import run_investigation
from app.orchestrator.persona import generate_persona_story


def generate_story(
    movement_event,
    role,
    persona_prompt,
):
    diagnostic_payload = run_investigation(movement_event)

    return generate_persona_story(
        diagnostic_payload=diagnostic_payload,
        role=role,
        persona_prompt=persona_prompt,
    )