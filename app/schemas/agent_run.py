from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class AgentRunResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    agent_id: UUID
    agent_version_id: UUID
    trace_id: str | None = None
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_context: dict | None = None
    output_payload: dict | None = None
    error_message: str | None = None
    created_at: datetime