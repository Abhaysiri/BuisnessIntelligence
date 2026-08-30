from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class InvestigationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    movement_event_id: UUID
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime