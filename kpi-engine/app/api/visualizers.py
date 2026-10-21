"""
Vega-Lite Chart Builders (§6.2, §7.3)
Generates curated declarative visualization specifications for KPI trends,
dimensional drivers, and timelines directly rendered in the React dashboard.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/visualizations", tags=["Visualizations"])


class VisualizationSpec(BaseModel):
    name: str
    description: Optional[str] = None
    vega_lite_spec: Dict[str, Any]


def build_kpi_trend(payload: Dict[str, Any]) -> VisualizationSpec:
    """Builds Vega-Lite spec for KPI actual vs. expected baseline with uncertainty error bands."""
    trend_data = payload.get("trend_data")
    if not trend_data and "metadata" in payload:
        trend_data = payload["metadata"].get("trend_data", [])

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "KPI Trend with Expected Bounds",
        "data": {"values": trend_data},
        "width": 460,
        "height": 220,
        "layer": [
            {
                "mark": {"type": "errorband", "opacity": 0.2},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal", "title": "Date"},
                    "y": {"field": "lower_bound", "type": "quantitative", "title": "KPI Value"},
                    "y2": {"field": "upper_bound"},
                },
            },
            {
                "mark": {"type": "line", "strokeDash": [5, 5]},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal"},
                    "y": {"field": "expected_value", "type": "quantitative"},
                    "color": {"value": "#888"},
                },
            },
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal"},
                    "y": {"field": "actual_value", "type": "quantitative"},
                    "color": {"value": "#1f77b4"},
                },
            },
        ],
    }

    return VisualizationSpec(
        name="KPI Trend",
        description="Trend of the KPI over time compared to expected bounds.",
        vega_lite_spec=spec,
    )


def build_dimensional_breakdown(payload: Dict[str, Any]) -> VisualizationSpec:
    """Builds Vega-Lite bar chart of dimensional deltas."""
    dimensions_data = payload.get("dimensions")
    if not dimensions_data and "metadata" in payload:
        dimensions_data = payload["metadata"].get("dimensions", [])

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Dimensional Breakdown",
        "data": {"values": dimensions_data},
        "width": 460,
        "height": 220,
        "mark": "bar",
        "encoding": {
            "x": {"field": "value", "type": "quantitative", "title": "Change"},
            "y": {"field": "dimension", "type": "nominal", "sort": "-x", "title": "Dimension"},
            "color": {
                "condition": {"test": "datum.value > 0", "value": "#2ca02c"},
                "value": "#d62728",
            },
        },
    }

    return VisualizationSpec(
        name="Dimensional Breakdown",
        description="Where did the KPI change across dimensions?",
        vega_lite_spec=spec,
    )


def build_driver_contribution(payload: Dict[str, Any]) -> VisualizationSpec:
    """Builds Vega-Lite bar chart attributing impact across top candidate drivers."""
    drivers_in_payload = payload.get("drivers", [])
    drivers_data = []

    for d in drivers_in_payload:
        drivers_data.append({
            "driver": d.get("name") or d.get("driver"),
            "contribution_absolute": d.get("contribution_absolute", 0),
            "contribution_percentage": d.get("contribution_percentage", 0),
            "confidence": d.get("diagnostic_confidence") or d.get("confidence", 0),
        })

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Driver Contribution",
        "data": {"values": drivers_data},
        "width": 460,
        "height": 220,
        "mark": "bar",
        "encoding": {
            "x": {"field": "contribution_absolute", "type": "quantitative", "title": "Impact"},
            "y": {"field": "driver", "type": "nominal", "sort": "-x", "title": "Driver"},
            "color": {
                "field": "confidence",
                "type": "quantitative",
                "scale": {"scheme": "blues"},
                "title": "Confidence",
            },
            "tooltip": [
                {"field": "driver", "type": "nominal"},
                {"field": "contribution_absolute", "type": "quantitative", "title": "Absolute Impact"},
                {"field": "contribution_percentage", "type": "quantitative", "title": "Percentage Impact"},
                {"field": "confidence", "type": "quantitative", "title": "Confidence Score"},
            ],
        },
    }

    return VisualizationSpec(
        name="Driver Contribution",
        description="Root-cause driver attribution breakdown.",
        vega_lite_spec=spec,
    )


@router.post("", response_model=List[VisualizationSpec])
def generate_visualizations(payload: Dict[str, Any] = Body(...)):
    """Accepts a DiagnosticPayload and returns curated Vega-Lite specs."""
    specs = []
    if payload.get("trend_data") or (payload.get("metadata", {}).get("trend_data")):
        specs.append(build_kpi_trend(payload))
    if payload.get("drivers"):
        specs.append(build_driver_contribution(payload))
    if payload.get("dimensions") or (payload.get("metadata", {}).get("dimensions")):
        specs.append(build_dimensional_breakdown(payload))

    # Fallback to trend + drivers if not empty
    if not specs:
        specs = [build_kpi_trend(payload), build_driver_contribution(payload)]

    return specs
