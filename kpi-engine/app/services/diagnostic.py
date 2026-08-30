from app.orchestrator.graph import investigation_graph
from app.schemas.diagnostic import DiagnosticPayload, Uncertainty

# In-memory repository for diagnostic payloads
_DIAGNOSTIC_STORE: dict[str, DiagnosticPayload] = {}


def run_investigation(movement_event) -> DiagnosticPayload:
    result = investigation_graph.invoke({
        "movement": movement_event,
        "findings": [],
    })

    payload: DiagnosticPayload = result["diagnostic_payload"]
    if payload:
        _DIAGNOSTIC_STORE[payload.incident_id] = payload

    return payload


def get_diagnostic_payload(diagnostic_payload_id: str) -> DiagnosticPayload:
    if diagnostic_payload_id in _DIAGNOSTIC_STORE:
        return _DIAGNOSTIC_STORE[diagnostic_payload_id]

    # Return default/empty diagnostic if not found in cache
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