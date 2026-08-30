from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AgentFindingResponse(BaseModel):
    id: UUID
    agent_run_id: UUID
    finding_type: str
    claim: str
    metric_name: str | None = None
    dimension: dict | None = None
    observed_value: Decimal | None = None
    baseline_value: Decimal | None = None
    absolute_change: Decimal | None = None
    percentage_change: Decimal | None = None
    confidence: Decimal | None = None
    time_start: datetime | None = None
    time_end: datetime | None = None
    source_count: int
    status: str
    raw_payload: dict
    created_at: datetime