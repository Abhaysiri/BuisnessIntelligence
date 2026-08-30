from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel


class DriverCandidateResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    name: str
    driver_type: str | None = None
    contribution_absolute: Decimal | None = None
    contribution_percentage: Decimal | None = None
    temporal_validity: bool | None = None
    dependency_validity: bool | None = None
    evidence_score: Decimal | None = None
    diagnostic_confidence: Decimal | None = None
    rank: int | None = None
    status: str
    metadata: dict