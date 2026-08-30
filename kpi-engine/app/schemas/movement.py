from datetime import datetime
from pydantic import BaseModel, Field


class KPIMovementEvent(BaseModel):
    event_id: str
    kpi_id: str

    analysis_start: datetime
    analysis_end: datetime

    observed_value: float
    expected_value: float

    absolute_change: float
    percentage_change: float

    statistical_score: float | None = None
    materiality_status: str

    dimensions: list[str] = Field(default_factory=list)