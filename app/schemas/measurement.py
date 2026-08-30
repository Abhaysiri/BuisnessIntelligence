from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MeasurementResponse(BaseModel):
    id: UUID
    kpi_id: UUID
    kpi_version_id: UUID
    observed_at: datetime
    period_start: datetime | None = None
    period_end: datetime | None = None
    value: Decimal
    unit: str
    currency: str | None = None
    dimensions: dict