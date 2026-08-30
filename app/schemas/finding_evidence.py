from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FindingEvidenceResponse(BaseModel):
    id: UUID
    finding_id: UUID
    source_id: UUID | None = None
    ingestion_run_id: UUID | None = None
    document_id: UUID | None = None
    source_record_identifier: str | None = None
    evidence_type: str
    evidence_timestamp: datetime | None = None
    metric_name: str | None = None
    observed_value: Decimal | None = None
    baseline_value: Decimal | None = None
    evidence_text: str | None = None
    source_uri: str | None = None
    metadata: dict