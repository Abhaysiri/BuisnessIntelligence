"""
End-to-End Medallion Ingestion Pipeline (§2.1, §2.2, §2.3, §2.4, §2.5)
Coordinates:
Bronze (MinIO WORM) -> Silver (Polars Vectorized Normalization) -> Imputation Hierarchy -> Validation Gates -> Quarantine -> DQ Scoring -> Gold Canonical Storage.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import polars as pl
import pandas as pd
from pydantic import BaseModel, Field

import sys
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from .bronze import BronzeStore, print_canonical_ddl
    from .silver import SilverProcessor
    from .imputation import TimeSeriesImputer
except (ImportError, ValueError):
    from bronze import BronzeStore, print_canonical_ddl
    from silver import SilverProcessor
    from imputation import TimeSeriesImputer

# Dynamic import for data-validity directory
import importlib.util
validity_dir = os.path.abspath(os.path.join(project_root, "data-validity"))

def _load_validity_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(validity_dir, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

val_mod = _load_validity_module("validation_mod", "validation.py")
ValidationGateManager = val_mod.ValidationGateManager
ValidationResult = val_mod.ValidationResult

quar_mod = _load_validity_module("quarantine_mod", "quarantine.py")
QuarantineStore = quar_mod.QuarantineStore
print_quarantine_ddl = quar_mod.print_quarantine_ddl

score_mod = _load_validity_module("scoring_mod", "scoring.py")
DQScorer = score_mod.DQScorer
DQScoreResult = score_mod.DQScoreResult


logger = logging.getLogger(__name__)


class IngestionBatchResult(BaseModel):
    batch_status: str  # "ADMITTED_TO_GOLD", "QUARANTINED", "DEGRADED"
    tenant_id: str
    kpi_id: str
    total_records_ingested: int
    gold_records_count: int
    quarantined_count: int
    is_imputed_count: int
    dq_score: float
    data_quality_status: str
    bronze_storage: Dict[str, Any]
    validation_verdict: Dict[str, Any]
    dq_details: Dict[str, Any]
    imputation_summary: Dict[str, Any]
    gold_records: List[Dict[str, Any]] = Field(default_factory=list)


class MedallionIngestionPipeline:
    """
    Complete Medallion Ingestion Pipeline.
    """

    def __init__(
        self,
        minio_endpoint: str = "localhost:19000",
        minio_access_key: str = "minioadmin",
        minio_secret_key: str = "minioadmin",
        bucket_name: str = "bronze-telemetry",
        default_cadence: str = "daily",
    ):
        self.bronze_store = BronzeStore(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            bucket_name=bucket_name,
        )
        self.silver_processor = SilverProcessor(default_cadence=default_cadence)
        self.imputer = TimeSeriesImputer(cadence=default_cadence)
        self.validator = ValidationGateManager()
        self.quarantine_store = QuarantineStore()
        self.dq_scorer = DQScorer()
        self.default_cadence = default_cadence

        # In-memory simulated Gold canonical storage
        self._gold_store: List[Dict[str, Any]] = []

    def print_all_ddl(self) -> Dict[str, str]:
        """Print all Supabase DDLs (canonical and quarantine)."""
        c_ddl = print_canonical_ddl()
        q_ddl = print_quarantine_ddl()
        return {
            "canonical_measurements": c_ddl,
            "quarantine_measurements": q_ddl,
        }

    def ingest_payload(
        self,
        raw_payload: Union[List[Dict[str, Any]], Dict[str, Any]],
        tenant_id: str,
        kpi_id: str,
        cadence: Optional[str] = None,
        baseline_30d: Optional[List[float]] = None,
        source_ip: str = "127.0.0.1",
        client_cert_fingerprint: Optional[str] = None,
    ) -> IngestionBatchResult:
        """
        Execute end-to-end Medallion ingestion pipeline.
        """
        active_cadence = cadence or self.default_cadence
        ingest_time = datetime.now(timezone.utc)

        # ----------------------------------------------------
        # 1. Bronze Layer (Immutable WORM Raw Storage)
        # ----------------------------------------------------
        bronze_res = self.bronze_store.store_raw_payload(
            raw_payload=raw_payload,
            tenant_id=tenant_id,
            kpi_id=kpi_id,
            source_ip=source_ip,
            client_cert_fingerprint=client_cert_fingerprint,
        )

        # ----------------------------------------------------
        # 2. Silver Layer (Polars Vectorized Normalization)
        # ----------------------------------------------------
        silver_df = self.silver_processor.normalize_and_cleanse(
            raw_payload=raw_payload,
            tenant_id=tenant_id,
            kpi_id=kpi_id,
            cadence=active_cadence,
        )

        # ----------------------------------------------------
        # 3. Imputation Hierarchy (§2.5)
        # ----------------------------------------------------
        imputer = TimeSeriesImputer(cadence=active_cadence)
        imputed_df, imputation_summary = imputer.regularize_and_impute(
            silver_df,
            tenant_id=tenant_id,
            kpi_id=kpi_id,
        )

        # Convert to list of dict records for validation gates
        records_to_validate = imputed_df.to_dicts()
        total_records = len(records_to_validate)

        # ----------------------------------------------------
        # 4. Multi-Tier Validation Gates (§2.2)
        # ----------------------------------------------------
        val_res = self.validator.validate_batch(
            records=records_to_validate,
            baseline_30d=baseline_30d,
            ingest_time=ingest_time,
        )

        # ----------------------------------------------------
        # 5. Quarantine Handling (§2.3) & DQ Scoring (§2.4)
        # ----------------------------------------------------
        quarantined_count = 0
        if not val_res.is_valid:
            for qr in val_res.quarantine_records:
                self.quarantine_store.quarantine(
                    tenant_id=tenant_id,
                    kpi_id=kpi_id,
                    raw_payload=qr.get("raw_payload", {}),
                    failed_tier=qr.get("failed_tier", val_res.failed_tier or "UNKNOWN"),
                    error_code=qr.get("error_code", val_res.error_code or "ERR_VALIDATION"),
                    error_message=qr.get("error_message", val_res.error_message or "Validation gate failed"),
                )
                quarantined_count += 1

        # Compute DQ score (§2.4)
        missing_ratio = imputation_summary.get("missing_ratio", 0.0)
        stl_eligible = imputation_summary.get("stl_eligible", True)

        s_struct = val_res.tier_scores.get("struct", 1.0)
        s_range = val_res.tier_scores.get("range", 1.0)

        # Temporal continuity score reflects un-interrupted observations and STL eligibility
        if missing_ratio > 0:
            penalty = 0.50 if not stl_eligible else 0.0
            s_temp = max(0.0, min(1.0, val_res.tier_scores.get("temp", 1.0) - missing_ratio - penalty))
        else:
            s_temp = val_res.tier_scores.get("temp", 1.0)

        # Reconciliation score reflects completeness of dimensional observations across timestamps
        if missing_ratio > 0.20:
            s_reconcile = max(0.0, min(1.0, val_res.tier_scores.get("reconcile", 1.0) - missing_ratio))
        else:
            s_reconcile = val_res.tier_scores.get("reconcile", 1.0)

        s_completeness = max(0.0, 1.0 - missing_ratio)

        dq_score_res = self.dq_scorer.compute_dq_score(
            s_struct=s_struct,
            s_range=s_range,
            s_temp=s_temp,
            s_reconcile=s_reconcile,
            s_completeness=s_completeness,
        )

        # ----------------------------------------------------
        # 6. Gold Layer Canonical Storage Insertion
        # ----------------------------------------------------
        gold_records = []
        if val_res.is_valid and dq_score_res.data_quality_status != "INVALID":
            for row in records_to_validate:
                gold_row = {
                    "tenant_id": row["tenant_id"],
                    "kpi_id": row["kpi_id"],
                    "observed_at": row["observed_at_str"],
                    "value": row["value"],
                    "dimensions": row["dimensions"],
                    "is_imputed": row["is_imputed"],
                    "dq_score": dq_score_res.dq_score,
                    "created_at": ingest_time.isoformat(),
                }
                self._gold_store.append(gold_row)
                gold_records.append(gold_row)
            
            batch_status = "ADMITTED_TO_GOLD" if dq_score_res.data_quality_status == "VALID" else "DEGRADED"
        else:
            batch_status = "QUARANTINED"

        imputed_count = int(imputed_df.filter(pl.col("is_imputed") == True).height) if imputed_df.height > 0 else 0

        return IngestionBatchResult(
            batch_status=batch_status,
            tenant_id=tenant_id,
            kpi_id=kpi_id,
            total_records_ingested=total_records,
            gold_records_count=len(gold_records),
            quarantined_count=quarantined_count,
            is_imputed_count=imputed_count,
            dq_score=dq_score_res.dq_score,
            data_quality_status=dq_score_res.data_quality_status,
            bronze_storage=bronze_res,
            validation_verdict={
                "is_valid": val_res.is_valid,
                "passed_tiers": val_res.passed_tiers,
                "failed_tier": val_res.failed_tier,
                "error_code": val_res.error_code,
                "error_message": val_res.error_message,
                "drift_telemetry": val_res.drift_telemetry,
            },
            dq_details=dq_score_res.model_dump(),
            imputation_summary=imputation_summary,
            gold_records=gold_records,
        )
