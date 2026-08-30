import operator
from typing import Annotated, TypedDict

from app.schemas.findings import AgentFinding
from app.schemas.movement import KPIMovementEvent
from app.schemas.diagnostic import DiagnosticPayload


class InvestigationState(TypedDict, total=False):
    movement: KPIMovementEvent
    findings: Annotated[list[AgentFinding], operator.add]
    analytical_results: list[dict]
    contradictions: list[dict]
    diagnostic_payload: DiagnosticPayload | None