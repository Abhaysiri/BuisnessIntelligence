from app.schemas.findings import AgentFinding
from app.schemas.movement import KPIMovementEvent


def calculate_contribution(finding: AgentFinding, movement: KPIMovementEvent) -> dict:
    """
    Computes absolute change and the percentage of the overall KPI movement
    attributable to the specific dimension slice identified in the finding.
    """
    dim_delta = None
    if finding.absolute_change is not None:
        dim_delta = finding.absolute_change
    elif finding.observed_value is not None and finding.baseline_value is not None:
        dim_delta = finding.observed_value - finding.baseline_value

    pct_of_movement = None
    if dim_delta is not None and movement.absolute_change and movement.absolute_change != 0:
        pct_of_movement = round((dim_delta / movement.absolute_change) * 100.0, 2)

    return {
        "absolute_contribution": dim_delta,
        "percentage_of_movement": pct_of_movement,
        "is_primary_driver": (pct_of_movement is not None and abs(pct_of_movement) >= 20.0)
    }
