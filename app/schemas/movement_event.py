from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MovementEventResponse(BaseModel):
    id: UUID
    organization_id: UUID
    kpi_id: UUID
    kpi_version_id: UUID
    baseline_observation_id: UUID | None = None
    detected_at: datetime
    analysis_start: datetime | None = None
    analysis_end: datetime | None = None
    observed_value: Decimal | None = None
    expected_value: Decimal | None = None
    absolute_change: Decimal | None = None
    percentage_change: Decimal | None = None
    statistical_score: Decimal | None = None
    business_impact: Decimal | None = None
    status: str
    metadata: dict