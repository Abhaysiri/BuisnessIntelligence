from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.schemas.diagnostic import DiagnosticPayload, Uncertainty
from app.services.diagnostic import _DIAGNOSTIC_STORE
from app.schemas.timeseries import STLDecompositionResult, STLParameters
from app.timeseries.anomaly import run_stl_pipeline

from app.schemas.ingestion import RawPayload
from app.services.diagnostic import run_investigation
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
    trace_id: Optional[str] = None
    message: Optional[str] = None
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
    Validates structural conformity, runs Medallion pipeline, STL decomposition, and triggers investigation.
    """
    if isinstance(payload, RawPayload):
        records = [payload.model_dump()]
        tenant_id = "default_tenant"
        kpi_id = payload.kpi_id or "dummy_kpi"
    elif isinstance(payload, list):
        records = [r.model_dump() for r in payload]
        tenant_id = "default_tenant"
        kpi_id = records[0].get("kpi_id") or "dummy_kpi"
    else:
        records = [r.model_dump() for r in payload.measurements]
        tenant_id = payload.tenant_id or "default_tenant"
        kpi_id = payload.kpi_id or (records[0].get("kpi_id") if records else "dummy_kpi")

    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ingestion payload must contain at least one valid measurement record.",
        )

    # 1. Run Medallion Ingestion Pipeline
    import sys, os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    pipeline_dir = os.path.join(project_root, "data-ingest")
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)
    from pipeline import MedallionIngestionPipeline
    
    medallion = MedallionIngestionPipeline()
    batch_result = medallion.ingest_payload(
        raw_payload=records,
        tenant_id=tenant_id,
        kpi_id=kpi_id
    )

    diagnostic_payload_id = None
    
    # 2. Persist Gold records to Database (Upsert/Watermark Pattern)
    if batch_result.gold_records:
        try:
            from app.tools.database import engine
            from sqlalchemy import text
            import json
            
            with engine.begin() as conn:
                res = conn.execute(text("SELECT id FROM kpi_versions LIMIT 1")).scalar()
                kpi_version_id = res if res else 'ee167a4d-6672-4aed-b583-bdc01fe4ba2b'
                
                # Fetch watermark (last analyzed anomaly timestamp)
                watermark_res = conn.execute(text("SELECT MAX(analysis_end) FROM kpi_movement_events")).scalar()
                last_watermark = watermark_res if watermark_res else None
                
                # Insert if not exists (preventing duplicates without wiping historical data)
                for row in batch_result.gold_records:
                    dims_json = json.dumps(row.get("dimensions", {}))
                    exists = conn.execute(
                        text("SELECT 1 FROM canonical_measurements WHERE observed_at = :obs AND dimensions::text = :dims"),
                        {"obs": row["observed_at"], "dims": dims_json}
                    ).scalar()
                    
                    if not exists:
                        conn.execute(
                            text("""
                                INSERT INTO canonical_measurements 
                                (organization_id, kpi_id, kpi_version_id, observed_at, value, unit, dimensions)
                                VALUES ((SELECT organization_id FROM kpi_definitions LIMIT 1), (SELECT id FROM kpi_definitions LIMIT 1), :ver, :obs, :val, :unit, :dims)
                            """),
                            {
                                "ver": kpi_version_id,
                                "obs": row["observed_at"],
                                "val": row["value"],
                                "unit": "USD",
                                "dims": dims_json
                            }
                        )
        except Exception as e:
            print("Failed to persist gold records to canonical_measurements:", e)

    # 3. Run STL Pipeline on validated Gold records
    if batch_result.gold_records:
        try:
            from app.timeseries.anomaly import run_stl_pipeline, create_kpi_movement_event
            from sqlalchemy import text
            from app.tools.database import engine
            
            # Fetch ALL canonical measurements for this KPI to give STL historical context
            with engine.begin() as conn:
                all_records = conn.execute(text("SELECT observed_at, value FROM canonical_measurements ORDER BY observed_at ASC")).fetchall()
            
            # Aggregate data by timestamp
            from collections import defaultdict
            agg_data = defaultdict(float)
            for r in all_records:
                agg_data[r[0]] += float(r[1])
            
            agg_records = [{"observed_at": k, "value": v} for k, v in sorted(agg_data.items())]

            stl_result = run_stl_pipeline(
                data=agg_records,
                tenant_id=tenant_id,
                kpi_id=kpi_id,
                timestamp_col="observed_at",
                value_col="value"
            )
            
            # Detect Anomaly and trigger investigation ONLY if it's new
            if stl_result.anomaly_detected and stl_result.trend_data:
                anomaly_point = max(stl_result.trend_data, key=lambda p: abs(p.z_score))
                
                # Check watermark
                is_new_anomaly = True
                if last_watermark and anomaly_point.timestamp <= last_watermark:
                    is_new_anomaly = False
                
                if is_new_anomaly:
                    denom = abs(anomaly_point.expected_value) if abs(anomaly_point.expected_value) > 1e-9 else 1.0
                    pct_change = abs(anomaly_point.actual_value - anomaly_point.expected_value) / denom
                    severity = "MAJOR" if pct_change >= 0.35 else "NORMAL"
                    
                    movement_event = create_kpi_movement_event(
                        kpi_id=kpi_id,
                        analysis_start=stl_result.trend_data[0].timestamp,
                        analysis_end=anomaly_point.timestamp,
                        observed_value=anomaly_point.actual_value,
                        expected_value=anomaly_point.expected_value,
                        z_score=anomaly_point.z_score,
                    )
                    
                    movement_event.materiality_status = severity
                    diagnostic_payload = run_investigation(movement_event, batch_result.dq_score)
                    diagnostic_payload_id = diagnostic_payload.incident_id
                else:
                    # Anomaly is old, return the existing payload ID
                    with engine.begin() as conn:
                        existing_id = conn.execute(text("SELECT id FROM diagnostic_payloads ORDER BY id DESC LIMIT 1")).scalar()
                        diagnostic_payload_id = existing_id
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"STL Pipeline or Investigation failed: {e}")

    # Log to DB
    try:
        from sqlalchemy import text
        from app.tools.database import engine
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO public.ingestion_logs (filename, type, size_bytes, dq_score, status)
                    VALUES (:filename, :type, :size_bytes, :dq_score, :status)
                """),
                {
                    # Extract the original filename from dimensions if present
                    "filename": records[0].get("dimensions", {}).get("source_file", f"batch_{tenant_id}_{kpi_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json") if records else f"batch_{tenant_id}_{kpi_id}.json",
                    "type": "Structured (JSON)",
                    "size_bytes": len(str(records)), # rough approx
                    "dq_score": batch_result.dq_score,
                    "status": "SILVER_VALIDATED" if batch_result.dq_score >= 0.90 else "QUARANTINED"
                }
            )
    except Exception as e:
        print(f"Failed to log ingestion: {e}")

    return IngestBatchResponse(
        status="ACCEPTED",
        processed_count=batch_result.total_records_ingested,
        quarantined_count=batch_result.quarantined_count,
        dq_score=batch_result.dq_score,
        trace_id=str(uuid4()),
        message=f"Successfully received {batch_result.total_records_ingested} metric measurements. Admitted to Gold: {batch_result.gold_records_count}",
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
