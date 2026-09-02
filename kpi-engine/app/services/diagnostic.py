from app.orchestrator.graph import investigation_graph
from app.schemas.diagnostic import DiagnosticPayload, Uncertainty

# In-memory repository for diagnostic payloads
_DIAGNOSTIC_STORE: dict[str, DiagnosticPayload] = {}


import json
from app.tools.database import engine
from sqlalchemy import text

def run_investigation(movement_event, dq_score: float = 1.0) -> DiagnosticPayload:
    result = investigation_graph.invoke({
        "movement": movement_event,
        "dq_score": dq_score,
        "findings": [],
    })

    payload: DiagnosticPayload = result.get("diagnostic_payload")
    if payload:
        _DIAGNOSTIC_STORE[payload.incident_id] = payload
        
        # Persist to Supabase
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO public.kpi_movement_events (
                            id, organization_id, kpi_id, kpi_version_id, detected_at, status, metadata
                        )
                        VALUES (
                            :id, (SELECT organization_id FROM kpi_definitions LIMIT 1), 
                            (SELECT id FROM kpi_definitions LIMIT 1), (SELECT id FROM kpi_versions LIMIT 1), 
                            CURRENT_TIMESTAMP, 'diagnosed', '{}'::jsonb
                        )
                        ON CONFLICT (id) DO NOTHING;

                        INSERT INTO public.investigations (id, organization_id, movement_event_id, status)
                        VALUES (:id, (SELECT organization_id FROM kpi_definitions LIMIT 1), :id, 'completed')
                        ON CONFLICT (id) DO NOTHING;
                        
                        INSERT INTO public.diagnostic_payloads (
                            id, investigation_id, kpi_id, kpi_version_id, 
                            overall_status, uncertainty_status, overall_confidence, abstain, payload
                        )
                        VALUES (
                            :id, :investigation_id, (SELECT id FROM kpi_definitions LIMIT 1), (SELECT id FROM kpi_versions LIMIT 1), 
                            :overall_status, :uncertainty_status, :overall_confidence, :abstain, :payload
                        )
                        ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                    """),
                    {
                        "id": payload.incident_id,
                        "investigation_id": payload.incident_id, # Reusing incident_id
                        "overall_status": 'abstain' if payload.uncertainty.abstain else (
                            'low_confidence' if payload.uncertainty.status == 'UNCERTAIN' else (
                                'contradictory' if payload.uncertainty.status == 'CONTRADICTORY' else 'diagnosed'
                            )
                        ),
                        "uncertainty_status": payload.uncertainty.status,
                        "overall_confidence": 1.0 if not payload.uncertainty.abstain else 0.0,
                        "abstain": payload.uncertainty.abstain,
                        "payload": payload.model_dump_json()
                    }
                )
        except Exception as e:
            print(f"Failed to persist diagnostic payload: {e}")

    return payload


def get_diagnostic_payload(diagnostic_payload_id: str) -> DiagnosticPayload:
    if diagnostic_payload_id in _DIAGNOSTIC_STORE:
        return _DIAGNOSTIC_STORE[diagnostic_payload_id]
        
    try:
        with engine.connect() as connection:
            res = connection.execute(
                text("SELECT payload FROM public.diagnostic_payloads WHERE id = :id"),
                {"id": diagnostic_payload_id}
            ).scalar()
            
            if res:
                if isinstance(res, str):
                    res = json.loads(res)
                return DiagnosticPayload(**res)
    except Exception as e:
        print(f"Failed to fetch diagnostic payload from DB: {e}")

    # Return default/empty diagnostic if not found in cache or DB
    return DiagnosticPayload(
        incident_id=diagnostic_payload_id,
        kpi_id="revenue",
        observed_value=0.0,
        expected_value=0.0,
        percentage_change=0.0,
        drivers=[],
        uncertainty=Uncertainty(
            status="UNKNOWN",
            abstain=True,
            reason=f"Diagnostic payload with ID {diagnostic_payload_id} not found."
        ),
        recommendations=[],
        lineage=[]
    )