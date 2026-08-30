"""
Bronze Layer: Raw Immutable Ingestion Store (MinIO WORM / Local Fallback)
Partitioning: tenant_id/kpi_id/YYYY/MM/DD/hh_raw_payload.json.zst (or .json)
Preserves unmodified source payloads with complete metadata (ingest timestamp, source IP, client cert/fingerprint, SHA256 checksum).
"""

import os
import io
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

try:
    from minio import Minio
    from minio.error import S3Error
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False

logger = logging.getLogger(__name__)

CANONICAL_MEASUREMENTS_DDL = """-- Gold Canonical Storage DDL (§2.1)
CREATE TABLE canonical_measurements (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    kpi_id VARCHAR(64) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    value NUMERIC(18, 6) NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    dq_score NUMERIC(5, 4) NOT NULL DEFAULT 1.0000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (tenant_id, kpi_id, observed_at, id)
) PARTITION BY RANGE (observed_at);
"""

def print_canonical_ddl() -> str:
    """Print the canonical_measurements DDL to console (§2.1 requirement)."""
    print("\n" + "=" * 80)
    print("PRINTING SUPABASE DDL (CANONICAL STORAGE - DO NOT EXECUTE DIRECTLY):")
    print(CANONICAL_MEASUREMENTS_DDL)
    print("=" * 80 + "\n")
    return CANONICAL_MEASUREMENTS_DDL


class BronzeStore:
    """
    MinIO WORM raw payload storage with resilient local in-memory/buffer fallback.
    """

    def __init__(
        self,
        endpoint: str = "localhost:19000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False,
        bucket_name: str = "bronze-telemetry",
        compress_zstd: bool = True,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.bucket_name = bucket_name
        self.compress_zstd = compress_zstd and HAS_ZSTD
        self._minio_client: Optional[Any] = None
        self._is_live: bool = False
        self._local_fallback_store: Dict[str, Dict[str, Any]] = {}

        self._init_minio_client()

    def _init_minio_client(self) -> None:
        """Attempt to connect to MinIO and ensure target bucket exists."""
        if not HAS_MINIO:
            self._is_live = False
            return

        try:
            client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            # Test connectivity by checking / creating bucket with short timeout
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
            self._minio_client = client
            self._is_live = True
            logger.info(f"Connected to MinIO at {self.endpoint}, bucket: {self.bucket_name}")
        except Exception as e:
            self._minio_client = None
            self._is_live = False
            logger.warning(f"MinIO connection failed ({self.endpoint}): {e}. Using resilient local fallback.")

    def is_connected(self) -> bool:
        """Check if MinIO is actively connected."""
        return self._is_live and self._minio_client is not None

    def generate_partition_path(
        self,
        tenant_id: str,
        kpi_id: str,
        ingest_time: datetime,
        use_zstd: bool = False,
    ) -> str:
        """
        Generate partition path: tenant_id/kpi_id/YYYY/MM/DD/hh_raw_payload.json(.zst)
        """
        year = ingest_time.strftime("%Y")
        month = ingest_time.strftime("%m")
        day = ingest_time.strftime("%d")
        hour = ingest_time.strftime("%H")
        ext = ".json.zst" if (use_zstd and HAS_ZSTD) else ".json"
        return f"{tenant_id}/{kpi_id}/{year}/{month}/{day}/{hour}_raw_payload{ext}"

    def store_raw_payload(
        self,
        raw_payload: Union[Dict[str, Any], List[Dict[str, Any]], str, bytes],
        tenant_id: str,
        kpi_id: str,
        source_ip: str = "127.0.0.1",
        client_cert_fingerprint: Optional[str] = None,
        observed_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Store raw uploaded payload immutably with metadata.
        """
        ingest_time = datetime.now(timezone.utc)
        if observed_time is None:
            observed_time = ingest_time

        # Serialize payload to JSON bytes
        if isinstance(raw_payload, (dict, list)):
            payload_str = json.dumps(raw_payload, default=str)
            raw_bytes = payload_str.encode("utf-8")
        elif isinstance(raw_payload, str):
            raw_bytes = raw_payload.encode("utf-8")
        else:
            raw_bytes = raw_payload

        payload_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        byte_size = len(raw_bytes)

        # Decide compression
        if self.compress_zstd and HAS_ZSTD:
            compressor = zstd.ZstdCompressor(level=3)
            stored_bytes = compressor.compress(raw_bytes)
            use_zstd = True
        else:
            stored_bytes = raw_bytes
            use_zstd = False

        object_path = self.generate_partition_path(tenant_id, kpi_id, ingest_time, use_zstd=use_zstd)

        metadata = {
            "tenant_id": tenant_id,
            "kpi_id": kpi_id,
            "ingest_timestamp": ingest_time.isoformat(),
            "source_ip": source_ip,
            "client_cert_fingerprint": client_cert_fingerprint or "none",
            "payload_sha256": payload_sha256,
            "raw_byte_size": byte_size,
            "compressed_byte_size": len(stored_bytes),
            "is_compressed": use_zstd,
            "compression_codec": "zstd" if use_zstd else "none",
            "bucket": self.bucket_name,
            "object_path": object_path,
        }

        # Try storing to MinIO
        stored_to_minio = False
        if self.is_connected():
            try:
                data_stream = io.BytesIO(stored_bytes)
                self._minio_client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_path,
                    data=data_stream,
                    length=len(stored_bytes),
                    metadata={
                        "x-amz-meta-sha256": payload_sha256,
                        "x-amz-meta-tenant-id": tenant_id,
                        "x-amz-meta-kpi-id": kpi_id,
                        "x-amz-meta-ingest-time": ingest_time.isoformat(),
                    },
                )
                stored_to_minio = True
            except Exception as e:
                logger.warning(f"Failed to write to MinIO ({object_path}): {e}. Falling back to local store.")
                self._is_live = False

        if not stored_to_minio:
            print("[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.")
            # Store in resilient in-memory / local fallback store
            self._local_fallback_store[object_path] = {
                "bytes": stored_bytes,
                "metadata": metadata,
                "raw_bytes": raw_bytes,
            }
            metadata["storage_mode"] = "MOCK_LOCAL_FALLBACK"
            metadata["is_mock"] = True
        else:
            metadata["storage_mode"] = "MINIO_WORM"
            metadata["is_mock"] = False

        return {
            "status": "STORED",
            "uri": f"s3://{self.bucket_name}/{object_path}",
            "metadata": metadata,
        }

    def retrieve_raw_payload(self, object_path: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Retrieve raw payload from MinIO or fallback store.
        """
        if self.is_connected():
            try:
                response = self._minio_client.get_object(self.bucket_name, object_path)
                data = response.read()
                response.close()
                response.release_conn()
                if object_path.endswith(".zst") and HAS_ZSTD:
                    decompressor = zstd.ZstdDecompressor()
                    data = decompressor.decompress(data)
                return data, {"source": "MINIO_WORM", "object_path": object_path}
            except Exception as e:
                logger.warning(f"Error fetching from MinIO: {e}")

        # Try local fallback
        if object_path in self._local_fallback_store:
            record = self._local_fallback_store[object_path]
            data = record.get("raw_bytes")
            if data is None:
                stored = record["bytes"]
                if record["metadata"].get("is_compressed") and HAS_ZSTD:
                    decompressor = zstd.ZstdDecompressor()
                    data = decompressor.decompress(stored)
                else:
                    data = stored
            return data, record["metadata"]

        raise KeyError(f"Payload not found at path: {object_path}")
