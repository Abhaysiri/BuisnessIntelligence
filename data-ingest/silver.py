"""
Silver Layer: Normalized In-Memory Cleansing Engine (Polars Vectorized)
Performs vectorized type casting, ISO-8601 UTC timestamp regularization,
cadence boundary flooring, and dimension hash standardization (dim_hash = SHA256(dim_key + dim_value)).
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import polars as pl


def compute_dimension_hash(dimensions: Union[Dict[str, Any], str, None]) -> str:
    """
    Standardize dimension hash: dim_hash = SHA256(sum(dim_key + dim_value) sorted).
    """
    if not dimensions:
        return hashlib.sha256(b"").hexdigest()

    if isinstance(dimensions, str):
        try:
            dims = json.loads(dimensions)
        except Exception:
            return hashlib.sha256(dimensions.encode("utf-8")).hexdigest()
    else:
        dims = dimensions

    if not isinstance(dims, dict):
        return hashlib.sha256(str(dims).encode("utf-8")).hexdigest()

    # Sort keys for deterministic hashing: SHA256(dim_key + dim_value)
    items = sorted(dims.items(), key=lambda x: str(x[0]))
    concat_str = "".join(f"{k}:{v}" for k, v in items)
    return hashlib.sha256(concat_str.encode("utf-8")).hexdigest()


def floor_timestamp_to_cadence(dt: datetime, cadence: str) -> datetime:
    """
    Floor a datetime object to registered cadence boundaries in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    cadence_lower = cadence.lower()
    if cadence_lower in ("hourly", "1h", "hour"):
        return dt.replace(minute=0, second=0, microsecond=0)
    elif cadence_lower in ("daily", "1d", "day"):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif cadence_lower in ("weekly", "1w", "week"):
        # Floor to Monday 00:00:00
        days_to_subtract = dt.weekday()
        floored = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        return floored - timedelta(days=days_to_subtract)
    elif cadence_lower in ("monthly", "1m", "month"):
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif cadence_lower in ("quarterly", "1q", "quarter"):
        quarter_month = ((dt.month - 1) // 3) * 3 + 1
        return dt.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default daily
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class SilverProcessor:
    """
    Polars vectorized normalization and cleansing processor.
    """

    def __init__(self, default_cadence: str = "daily"):
        self.default_cadence = default_cadence

    def parse_observed_at(self, val: Any, cadence: str) -> datetime:
        """Parse various timestamp representations into floored UTC datetime."""
        if isinstance(val, datetime):
            dt = val
        elif isinstance(val, (int, float)):
            # Epoch milliseconds or seconds
            if val > 1e11:  # Milliseconds
                dt = datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(val, tz=timezone.utc)
        elif isinstance(val, str):
            # Parse ISO string
            cleaned = val.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(cleaned)
            except ValueError:
                from dateutil import parser
                dt = parser.parse(cleaned)
        else:
            raise ValueError(f"Unparseable timestamp: {val}")

        return floor_timestamp_to_cadence(dt, cadence)

    def normalize_and_cleanse(
        self,
        raw_payload: Union[List[Dict[str, Any]], Dict[str, Any], pl.DataFrame],
        tenant_id: Optional[str] = None,
        kpi_id: Optional[str] = None,
        cadence: Optional[str] = None,
    ) -> pl.DataFrame:
        """
        Convert raw payload into standardized, cleansed Polars DataFrame.
        """
        active_cadence = cadence or self.default_cadence

        # Extract list of dict records
        if isinstance(raw_payload, pl.DataFrame):
            records = raw_payload.to_dicts()
        elif isinstance(raw_payload, dict):
            if "data" in raw_payload and isinstance(raw_payload["data"], list):
                records = raw_payload["data"]
            elif "records" in raw_payload and isinstance(raw_payload["records"], list):
                records = raw_payload["records"]
            elif "series" in raw_payload and isinstance(raw_payload["series"], list):
                records = raw_payload["series"]
            else:
                records = [raw_payload]
        elif isinstance(raw_payload, list):
            records = raw_payload
        else:
            raise TypeError(f"Unsupported payload type: {type(raw_payload)}")

        if not records:
            # Return empty schema-compliant DataFrame
            return pl.DataFrame(
                schema={
                    "tenant_id": pl.Utf8,
                    "kpi_id": pl.Utf8,
                    "observed_at": pl.Datetime("ms", "UTC"),
                    "observed_at_str": pl.Utf8,
                    "value": pl.Float64,
                    "dimensions": pl.Utf8,
                    "dim_hash": pl.Utf8,
                    "is_imputed": pl.Boolean,
                }
            )

        cleaned_records = []
        for row in records:
            # Normalize tenant_id and kpi_id
            row_tenant = str(row.get("tenant_id") or tenant_id or "").strip()
            row_kpi = str(row.get("kpi_id") or row.get("metric_id") or kpi_id or "").strip()

            # Normalize timestamp
            raw_ts = row.get("observed_at") or row.get("timestamp") or row.get("date")
            if raw_ts is None:
                raise ValueError("Missing required timestamp field ('observed_at')")
            floored_dt = self.parse_observed_at(raw_ts, active_cadence)

            # Normalize value
            raw_val = row.get("value")
            if raw_val is None:
                val = None
            else:
                try:
                    val = float(raw_val)
                except (ValueError, TypeError):
                    val = float("nan")

            # Dimensions & hash
            dims = row.get("dimensions", {})
            dim_hash = compute_dimension_hash(dims)
            dims_str = json.dumps(dims, sort_keys=True) if isinstance(dims, dict) else str(dims or "{}")

            is_imputed = bool(row.get("is_imputed", False))

            cleaned_records.append(
                {
                    "tenant_id": row_tenant,
                    "kpi_id": row_kpi,
                    "observed_at": floored_dt,
                    "observed_at_str": floored_dt.isoformat(),
                    "value": val,
                    "dimensions": dims_str,
                    "dim_hash": dim_hash,
                    "is_imputed": is_imputed,
                }
            )

        # Build Polars DataFrame
        df = pl.DataFrame(
            cleaned_records,
            schema={
                "tenant_id": pl.Utf8,
                "kpi_id": pl.Utf8,
                "observed_at": pl.Datetime("ms", "UTC"),
                "observed_at_str": pl.Utf8,
                "value": pl.Float64,
                "dimensions": pl.Utf8,
                "dim_hash": pl.Utf8,
                "is_imputed": pl.Boolean,
            },
        )

        # Vectorized deduplication by (tenant_id, kpi_id, observed_at, dim_hash)
        # Keep last observed record
        df = df.unique(subset=["tenant_id", "kpi_id", "observed_at", "dim_hash"], keep="last")

        # Vectorized sort by observed_at
        df = df.sort("observed_at")

        return df
