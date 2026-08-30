from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

app = FastAPI(title="Visualizers API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VisualizationSpec(BaseModel):
    name: str
    description: Optional[str] = None
    vega_lite_spec: Dict[str, Any]

class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str
    title: str
    source_id: Optional[str] = None
    evidence_id: Optional[str] = None

def build_kpi_trend(payload: Dict[str, Any]) -> VisualizationSpec:
    """Build KPI Trend builder - Act 1"""
    # Look for trend_data in metadata if not at root
    trend_data = payload.get("trend_data")
    if not trend_data and "metadata" in payload:
        trend_data = payload["metadata"].get("trend_data", [])
        
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "KPI Trend with Expected Bounds",
        "data": {"values": trend_data},
        "width": "container",
        "height": 300,
        "layer": [
            {
                "mark": {"type": "errorband", "opacity": 0.2},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal", "title": "Date"},
                    "y": {"field": "lower_bound", "type": "quantitative", "title": "KPI Value"},
                    "y2": {"field": "upper_bound"}
                }
            },
            {
                "mark": {"type": "line", "strokeDash": [5, 5]},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal"},
                    "y": {"field": "expected_value", "type": "quantitative"},
                    "color": {"value": "#888"}
                }
            },
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "timestamp", "type": "temporal"},
                    "y": {"field": "actual_value", "type": "quantitative"},
                    "color": {"value": "#1f77b4"}
                }
            }
        ]
    }
    
    return VisualizationSpec(
        name="KPI Trend",
        description="Trend of the KPI over time compared to expected bounds.",
        vega_lite_spec=spec
    )

def build_dimensional_breakdown(payload: Dict[str, Any]) -> VisualizationSpec:
    """Build Dimensional Breakdown builder - Where did it change?"""
    # Extract from drivers or metadata
    dimensions_data = payload.get("dimensions")
    if not dimensions_data and "metadata" in payload:
        dimensions_data = payload["metadata"].get("dimensions", [])
        
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Dimensional Breakdown",
        "data": {"values": dimensions_data},
        "width": "container",
        "height": 300,
        "mark": "bar",
        "encoding": {
            "x": {"field": "value", "type": "quantitative", "title": "Change"},
            "y": {"field": "dimension", "type": "nominal", "sort": "-x", "title": "Dimension"},
            "color": {
                "condition": {"test": "datum.value > 0", "value": "#2ca02c"},
                "value": "#d62728"
            }
        }
    }
    
    return VisualizationSpec(
        name="Dimensional Breakdown",
        description="Where did the KPI change?",
        vega_lite_spec=spec
    )

def build_driver_contribution(payload: Dict[str, Any]) -> VisualizationSpec:
    """Build Driver Contribution builder - Why did it change?"""
    # We will map payload["drivers"] to the structure expected by the visualizer
    drivers_in_payload = payload.get("drivers", [])
    drivers_data = []
    
    for d in drivers_in_payload:
        drivers_data.append({
            "driver": d.get("name") or d.get("driver"),
            "contribution_absolute": d.get("contribution_absolute", 0),
            "contribution_percentage": d.get("contribution_percentage", 0),
            "confidence": d.get("diagnostic_confidence") or d.get("confidence", 0)
        })
    
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Driver Contribution",
        "data": {"values": drivers_data},
        "width": "container",
        "height": 300,
        "mark": "bar",
        "encoding": {
            "x": {"field": "contribution_absolute", "type": "quantitative", "title": "Impact"},
            "y": {"field": "driver", "type": "nominal", "sort": "-x", "title": "Driver"},
            "color": {
                "field": "confidence", 
                "type": "quantitative", 
                "scale": {"scheme": "blues"},
                "title": "Confidence"
            },
            "tooltip": [
                {"field": "driver", "type": "nominal"},
                {"field": "contribution_absolute", "type": "quantitative", "title": "Absolute Impact"},
                {"field": "contribution_percentage", "type": "quantitative", "title": "Percentage Impact"},
                {"field": "confidence", "type": "quantitative", "title": "Confidence Score"}
            ]
        }
    }
    
    return VisualizationSpec(
        name="Driver Contribution",
        description="Why did the KPI change?",
        vega_lite_spec=spec
    )

def build_timeline(payload: Dict[str, Any]) -> VisualizationSpec:
    """Build Timeline builder - When did it happen?"""
    events_data = payload.get("events")
    if not events_data and "metadata" in payload:
        events_data = payload["metadata"].get("events", [])
        
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Effect Timeline",
        "data": {"values": events_data},
        "width": "container",
        "height": 150,
        "mark": {"type": "circle", "size": 200},
        "encoding": {
            "x": {"field": "timestamp", "type": "temporal", "title": "Date"},
            "color": {"field": "event_type", "type": "nominal", "title": "Event Type"},
            "tooltip": [
                {"field": "timestamp", "type": "temporal"},
                {"field": "title", "type": "nominal"},
                {"field": "event_type", "type": "nominal"}
            ]
        }
    }
    
    return VisualizationSpec(
        name="Effect Timeline",
        description="When did the events happen?",
        vega_lite_spec=spec
    )

@app.post("/visualizations", response_model=List[VisualizationSpec])
async def generate_visualizations(payload: Dict[str, Any] = Body(...)):
    """
    Accepts a DiagnosticPayload and returns Vega-Lite specs.
    """
    specs = [
        build_kpi_trend(payload),
        build_dimensional_breakdown(payload),
        build_driver_contribution(payload),
        build_timeline(payload)
    ]
    return specs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
