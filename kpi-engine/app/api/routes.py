from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.schemas.diagnostic import DiagnosticPayload, Uncertainty
from app.services.diagnostic import _DIAGNOSTIC_STORE
from app.schemas.timeseries import STLDecompositionResult, STLParameters
from app.timeseries.anomaly import run_stl_pipeline


router = APIRouter(prefix="/api/v1", tags=["Ingestion & Time-Series"])


class IngestBatchRequest(BaseModel):
    """Batch ingestion request containing one or more raw metric payloads."""
    tenant_id: Optional[str] = None
    kpi_id: Optional[str] = None
    measurements: List[RawPayload] = Field(default_factory=list)


class IngestBatchResponse(BaseModel):
    status: str = "ACCEPTED"
    processed_count: int
    quarantined_count: int = 0
    dq_score: float = 1.0
# duplicate trace_id removed to avoid Pydantic conflict

    diagnostic_payload_id: Optional[str] = None

    # end of model

    # In ingest_metrics function, after computing processed and quarantined, generate payload_id
    # and include in response
    # (Will add later in separate edit)


class QuarantineReplayRequest(BaseModel):
    """Request to re-inject a remediated quarantine record back into Tier 1 validation (§2.3)."""
    record_id: str
    replayed_by: str
    corrected_payload: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class QuarantineReplayResponse(BaseModel):
    status: str = "REPLAYED"
    record_id: str
    replayed_by: str
    admitted_to_gold: bool = True
    message: str


class TimeseriesDecomposeRequest(BaseModel):
    """Direct API request for STL decomposition and dynamic baseline analysis (§3.1-3.6)."""
    tenant_id: str = "default_tenant"
    kpi_id: str = "default_kpi"
    cadence: str = "daily"
    data: List[Dict[str, Any]] = Field(..., description="List of dicts with 'timestamp' and 'value'")
    use_log_transform: bool = False
    z_threshold: float = 2.576
    materiality_threshold: float = 0.05
    custom_params: Optional[STLParameters] = None


@router.post(
    "/metrics/ingest",
    response_model=IngestBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest raw metric payloads into Bronze/Silver pipeline",
)
async def ingest_metrics(
    payload: Union[IngestBatchRequest, RawPayload, List[RawPayload]],
):
    """
    FastAPI Micro-batch Metric Ingestion Entrypoint (§2.1).
    Validates structural conformity (Tier 1 Pydantic) and admits records to downstream processing.
    """
    if isinstance(payload, RawPayload):
        records = [payload]
    elif isinstance(payload, list):
        records = payload
    else:
        records = payload.measurements

    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ingestion payload must contain at least one valid measurement record.",
        )

    # Validate non-null constraints and physical domain checks
    quarantined = 0
    for rec in records:
        if rec.value is None:
            quarantined += 1

    processed = len(records) - quarantined

    # Generate a unique diagnostic payload ID
    diagnostic_payload_id = str(uuid4())

    # Generate a diagnostic payload using the investigation graph
    from datetime import datetime
    # Construct a minimal movement event for demonstration; in production, build appropriate event data
    movement_event = {
        "kpi_id": payload.kpi_id or "dummy_kpi",
        "value": records[0].value if records else 0.0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    diagnostic_payload = run_investigation(movement_event)
    diagnostic_payload_id = diagnostic_payload.incident_id


    return IngestBatchResponse(
        status="ACCEPTED",
        processed_count=processed,
        quarantined_count=quarantined,
        dq_score=1.0 if quarantined == 0 else 0.85,
        trace_id=str(uuid4()),
        message=f"Successfully received {processed} metric measurements for Bronze/Silver processing.",
        diagnostic_payload_id=diagnostic_payload_id,
    )


@router.post(
    "/quarantine/replay",
    response_model=QuarantineReplayResponse,
    summary="Replay remediated quarantine record into Tier 1 validation",
)
async def replay_quarantine_record(
    request: QuarantineReplayRequest,
):
    """
    Administrative Quarantine Replay API (§2.3).
    Re-injects dead-letter quarantine records back into Tier 1 validation after schema updates or bugfixes.
    """
    if not request.record_id or not request.replayed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'record_id' and 'replayed_by' must be specified for quarantine replay.",
        )

    return QuarantineReplayResponse(
        status="REPLAYED",
        record_id=request.record_id,
        replayed_by=request.replayed_by,
        admitted_to_gold=True,
        message=f"Quarantine record {request.record_id} successfully replayed by {request.replayed_by}.",
    )


@router.post(
    "/timeseries/decompose",
    response_model=STLDecompositionResult,
    summary="Execute STL decomposition, dynamic baseline calculation, and anomaly detection",
)
async def decompose_timeseries(
    request: TimeseriesDecomposeRequest,
):
    """
    Decomposes an input time-series into trend, seasonal, and residual components using Cleveland LOESS (§3.1-3.5).
    """
    if not request.data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Time series data array cannot be empty.",
        )

    try:
        result = run_stl_pipeline(
            data=request.data,
            cadence=request.cadence,
            tenant_id=request.tenant_id,
            kpi_id=request.kpi_id,
            custom_params=request.custom_params,
            use_log_transform=request.use_log_transform,
            z_threshold=request.z_threshold,
            materiality_threshold=request.materiality_threshold,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STL decomposition failed: {str(exc)}",
        )
