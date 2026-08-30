from uuid import UUID
from pydantic import BaseModel


class KPIResponse(BaseModel):
    id: UUID
    organization_id: UUID
    kpi_key: str
    display_name: str
    description: str | None = None
    owner_role: str | None = None
    status: str