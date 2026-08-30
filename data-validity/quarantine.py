"""
Dead-Letter Quarantine & Replay Architecture (§2.3)
Diverts invalid metric records, tracks validation trace diagnostics,
and provides administrative replay logic to re-inject remediated records back into Tier 1.
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

QUARANTINE_MEASUREMENTS_DDL = """-- Quarantine Dead-Letter Store DDL (§2.3)
CREATE TABLE quarantine_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    kpi_id VARCHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    failed_tier VARCHAR(32) NOT NULL,
    error_code VARCHAR(64) NOT NULL,
    error_message TEXT NOT NULL,
    validation_trace JSONB NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    replayed_by VARCHAR(64)
);
"""

def print_quarantine_ddl() -> str:
    """Print the quarantine_measurements DDL to console (§2.3 requirement)."""
    print("\n" + "=" * 80)
    print("PRINTING SUPABASE DDL (QUARANTINE DEAD-LETTER STORE - DO NOT EXECUTE DIRECTLY):")
    print(QUARANTINE_MEASUREMENTS_DDL)
    print("=" * 80 + "\n")
    return QUARANTINE_MEASUREMENTS_DDL


class QuarantineRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    kpi_id: str
    raw_payload: Dict[str, Any]
    failed_tier: str
    error_code: str
    error_message: str
    validation_trace: Dict[str, Any]
    quarantined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    replayed_by: Optional[str] = None


class QuarantineStore:
    """
    Dead-letter store tracking quarantined metric failures with replay support.
    """

    def __init__(self):
        self._records: Dict[str, QuarantineRecord] = {}

    def quarantine(
        self,
        tenant_id: str,
        kpi_id: str,
        raw_payload: Dict[str, Any],
        failed_tier: str,
        error_code: str,
        error_message: str,
        validation_trace: Optional[Dict[str, Any]] = None,
    ) -> QuarantineRecord:
        """
        Record a rejected payload in the dead-letter quarantine store.
        """
        record = QuarantineRecord(
            tenant_id=tenant_id,
            kpi_id=kpi_id,
            raw_payload=raw_payload,
            failed_tier=failed_tier,
            error_code=error_code,
            error_message=error_message,
            validation_trace=validation_trace or {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "failed_tier": failed_tier,
                "error_code": error_code,
                "error_message": error_message,
            },
        )
        self._records[record.id] = record
        logger.warning(
            f"Quarantined record {record.id} [Tier: {failed_tier}, Code: {error_code}]: {error_message}"
        )
        return record

    def get_record(self, record_id: str) -> Optional[QuarantineRecord]:
        return self._records.get(record_id)

    def list_unresolved(self, tenant_id: Optional[str] = None, kpi_id: Optional[str] = None) -> List[QuarantineRecord]:
        results = [r for r in self._records.values() if not r.resolved]
        if tenant_id:
            results = [r for r in results if r.tenant_id == tenant_id]
        if kpi_id:
            results = [r for r in results if r.kpi_id == kpi_id]
        return results

    def replay(
        self,
        record_id: str,
        replayed_by: str = "admin_user",
        mutated_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Administrative Replay API logic (§2.3 POST /api/v1/quarantine/replay).
        Re-evaluates the quarantined record through validation gates.
        """
        record = self.get_record(record_id)
        if not record:
            return False, {"error": f"Quarantine record {record_id} not found"}

        payload_to_replay = mutated_payload if mutated_payload is not None else record.raw_payload

        # Lazy import to avoid circular dependencies
        try:
            from .validation import ValidationGateManager
        except (ImportError, ValueError):
            from validation import ValidationGateManager
        validator = ValidationGateManager()

        # Re-validate
        result = validator.validate_batch([payload_to_replay])

        if result.is_valid:
            record.resolved = True
            record.resolved_at = datetime.now(timezone.utc)
            record.replayed_by = replayed_by
            return True, {
                "record_id": record_id,
                "status": "REPLAYED_SUCCESSFULLY",
                "resolved_at": record.resolved_at.isoformat(),
                "replayed_by": replayed_by,
                "replayed_payload": payload_to_replay,
            }
        else:
            return False, {
                "record_id": record_id,
                "status": "REPLAY_FAILED_VALIDATION",
                "failed_tier": result.failed_tier,
                "error_code": result.error_code,
                "error_message": result.error_message,
            }
