import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.tools.database import engine

router = APIRouter(prefix="/api/v1/human-decisions", tags=["Human Decisions"])

class HumanDecisionRequest(BaseModel):
    decision: str = Field(..., description="Decision choice: approve, reject, delegate, request_changes")
    comment: Optional[str] = None
    correction_payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = Field("analyst_user", description="Identifier of the reviewer")

class HumanDecisionResponse(BaseModel):
    decision_id: str
    recommendation_id: str
    decision: str
    status: str
    comment: Optional[str] = None
    recorded_at: datetime
    message: str

VALID_DECISIONS = {"approve", "reject", "delegate", "request_changes"}
STATUS_MAP = {
    "approve": "approved",
    "reject": "rejected",
    "delegate": "delegated",
    "request_changes": "proposed",
}

# In-memory fallback if database tables don't exist yet
_HUMAN_DECISIONS_STORE: Dict[str, Dict[str, Any]] = {}

@router.post("/{recommendation_id}", response_model=HumanDecisionResponse)
def record_human_decision(
    recommendation_id: str,
    request: HumanDecisionRequest,
):
    """
    Action Review Decision API (§4.4, §7.1).
    Records human-in-the-loop approvals, rejections, or amendments for governed recommendations.
    """
    decision_lower = request.decision.lower().strip()
    if decision_lower not in VALID_DECISIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision '{request.decision}'. Must be one of: {sorted(list(VALID_DECISIONS))}",
        )

    decision_id = str(uuid.uuid4())
    recorded_at = datetime.now(timezone.utc)
    new_status = STATUS_MAP[decision_lower]

    decision_record = {
        "decision_id": decision_id,
        "recommendation_id": recommendation_id,
        "user_id": request.user_id or "analyst_user",
        "decision": decision_lower,
        "status": new_status,
        "comment": request.comment,
        "correction_payload": request.correction_payload or {},
        "recorded_at": recorded_at.isoformat(),
    }

    _HUMAN_DECISIONS_STORE[decision_id] = decision_record

    # Attempt PostgreSQL persistence if DB tables are present
    try:
        with engine.begin() as conn:
            # Check or create human_decisions table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS public.human_decisions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    recommendation_id VARCHAR(128) NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    decision VARCHAR(32) NOT NULL,
                    comment TEXT,
                    correction_payload JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
                );
            """))

            conn.execute(
                text("""
                    INSERT INTO public.human_decisions (id, recommendation_id, user_id, decision, comment, correction_payload)
                    VALUES (:id, :rec_id, :user_id, :decision, :comment, :payload)
                """),
                {
                    "id": decision_id,
                    "rec_id": recommendation_id,
                    "user_id": request.user_id or "analyst_user",
                    "decision": decision_lower,
                    "comment": request.comment,
                    "payload": json.dumps(request.correction_payload or {}),
                }
            )

            # Try updating recommendation status if recommendations table exists
            try:
                conn.execute(
                    text("UPDATE public.recommendations SET status = :status WHERE id = :id"),
                    {"status": new_status, "id": recommendation_id}
                )
            except Exception:
                pass
    except Exception as e:
        # Graceful fallback logged to terminal
        print(f"[HumanDecision] Note: DB persistence skipped/failed ({e}), decision kept in memory.")

    return HumanDecisionResponse(
        decision_id=decision_id,
        recommendation_id=recommendation_id,
        decision=decision_lower,
        status=new_status,
        comment=request.comment,
        recorded_at=recorded_at,
        message=f"Human decision '{decision_lower}' recorded successfully for recommendation {recommendation_id}."
    )

@router.get("/history", summary="Get recent human governance decisions")
def get_decision_history(limit: int = 50):
    """Retrieve decision audit history."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, recommendation_id, user_id, decision, comment, created_at FROM public.human_decisions ORDER BY created_at DESC LIMIT :lim"),
                {"lim": limit}
            ).mappings().all()
            if rows:
                return [dict(r) for r in rows]
    except Exception:
        pass
    return list(_HUMAN_DECISIONS_STORE.values())[-limit:]
