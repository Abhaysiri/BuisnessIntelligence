
from uuid import UUID

from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    agent_key: str
    display_name: str
    domain: str
    description: str | None = None
    active: bool