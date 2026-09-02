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
        role=payload_request.role,
        persona_prompt=payload_request.prompt,
    )
    try:
        from app.tools.database import engine
        from sqlalchemy import text
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO public.stories (diagnostic_payload_id, role, story_headline, story_body)
                    VALUES (:pid, :role, :headline, :body)
                """),
                {
                    "pid": diagnostic_payload_id,
                    "role": payload_request.role.value,
                    "headline": result.get("headline", ""),
                    "body": result.get("narrative", "")
                }
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to persist story: {e}")

    return result

from app.monitoring.feedback import submit_feedback, FeedbackRequest

@router.post("/persona/feedback")
def submit_persona_feedback(feedback: FeedbackRequest):
    success = submit_feedback(feedback)
    try:
        from app.tools.database import engine
        from sqlalchemy import text
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO public.feedback (diagnostic_payload_id, role, is_helpful, comments)
                    VALUES (:pid, :role, :is_helpful, :comments)
                """),
                {
                    # Use trace_id or fallback to generic uuid if it's not a valid uuid
                    "pid": feedback.trace_id, 
                    "role": feedback.reviewer_role,
                    "is_helpful": bool(feedback.verdict),
                    "comments": feedback.comments or ""
                }
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to persist feedback: {e}")
        
    return {"success": success}