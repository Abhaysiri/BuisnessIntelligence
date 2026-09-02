from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List, Dict, Any
from app.tools.database import engine

router = APIRouter(prefix="/api/v1/audit", tags=["Audit and Telemetry"])

@router.get("/ingestions")
async def get_ingestions():
    """Fetches unique ingestion logs grouped by filename, keeping latest status and computing total dupes."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT 
                    filename,
                    MAX(type) as type,
                    MAX(size_bytes) as size,
                    AVG(dq_score) as dq_score,
                    MAX(status) as status,
                    MAX(created_at) as timestamp,
                    COUNT(*) as count
                FROM public.ingestion_logs
                GROUP BY filename
                ORDER BY timestamp DESC
                LIMIT 100
            """))
            rows = []
            for row in result:
                r = dict(row._mapping)
                # Frontend expects friendly size and string timestamp
                size_mb = r["size"] / (1024 * 1024)
                r["size_str"] = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{(r['size']/1024):.2f} KB"
                r["timestamp_str"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if r["timestamp"] else "Unknown"
                rows.append(r)
            return {"ingestions": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics-history")
async def get_analytics_history():
    """Fetches past stories and their original diagnostic payload."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT s.id, s.diagnostic_payload_id, s.role, s.story_headline, s.story_body, s.created_at,
                       d.kpi_id, d.payload
                FROM public.stories s
                LEFT JOIN public.diagnostic_payloads d ON s.diagnostic_payload_id = d.id
                ORDER BY s.created_at DESC
                LIMIT 50
            """))
            return {"history": [dict(r._mapping) for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/major-events")
async def get_major_events():
    """Fetches major KPI movement events."""
    # Assuming kpi_movement_events exists in DB. Let's try to query it.
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT * FROM public.kpi_movement_events 
                WHERE severity = 'MAJOR'
                ORDER BY analysis_end DESC
                LIMIT 50
            """))
            return {"events": [dict(r._mapping) for r in result]}
    except Exception as e:
        # If it doesn't exist yet, return empty list safely
        print("Major events table error:", e)
        return {"events": []}

@router.get("/telemetry")
async def get_telemetry():
    """Fetches OpenTelemetry traces exported to Supabase."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT * FROM public.telemetry_traces
                ORDER BY created_at DESC
                LIMIT 100
            """))
            return {"traces": [dict(r._mapping) for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
