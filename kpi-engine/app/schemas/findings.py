from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source_id: str
    source_type: str

    metric: str | None = None
    value: float | None = None
    baseline: float | None = None

    timestamp: datetime | None = None

    record_id: str | None = None
    text: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentFinding(BaseModel):
    agent_name: str

    claim: str

    driver_type: str

    dimension: dict[str, str] = Field(default_factory=dict)

    observed_value: float | None = None
    baseline_value: float | None = None

    absolute_change: float | None = None
    percentage_change: float | None = None

    time_start: datetime | None = None
    time_end: datetime | None = None

    evidence: list[Evidence] = Field(default_factory=list)

    confidence: float = Field(ge=0, le=1)

    metadata: dict[str, Any] = Field(default_factory=dict)