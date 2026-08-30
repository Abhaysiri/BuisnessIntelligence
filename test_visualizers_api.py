import requests
import json
import uuid
from datetime import datetime, timedelta

def main():
    # Construct a real-looking DiagnosticPayload with added trend, dimensions, events in metadata
    
    now = datetime.utcnow()
    
    trend_data = [
        {
            "timestamp": (now - timedelta(days=i)).isoformat(),
            "actual_value": 1000 - (i * 10) + (i % 3 * 5),
            "expected_value": 1050 - (i * 10),
            "lower_bound": 1020 - (i * 10),
            "upper_bound": 1080 - (i * 10)
        }
        for i in range(30, -1, -1)
    ]
    
    dimensions = [
        {"dimension": "Europe", "value": -40000},
        {"dimension": "Asia", "value": -8000},
        {"dimension": "US", "value": -5000},
        {"dimension": "Latin America", "value": 2000},
    ]
    
    events = [
        {
            "timestamp": (now - timedelta(days=15)).isoformat(),
            "event_type": "Marketing Campaign",
            "title": "Summer Sale Started",
            "source_id": "mktg_sys_1",
            "evidence_id": "ev_123"
        },
        {
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "event_type": "Outage",
            "title": "Payment Gateway Down",
            "source_id": "eng_sys_1",
            "evidence_id": "ev_124"
        }
    ]
    
    payload = {
        "incident_id": str(uuid.uuid4()),
        "kpi_id": "revenue_weekly",
        "observed_value": 850000,
        "expected_value": 900000,
        "percentage_change": -5.55,
        "drivers": [
            {
                "driver_id": "drv_1",
                "name": "Conversion Rate Drop in Europe",
                "driver_type": "metric",
                "contribution_absolute": -40000,
                "contribution_percentage": -4.44,
                "diagnostic_confidence": 0.92,
                "supporting_findings": ["Drop in payment success"]
            },
            {
                "driver_id": "drv_2",
                "name": "Traffic Drop in Asia",
                "driver_type": "metric",
                "contribution_absolute": -8000,
                "contribution_percentage": -0.88,
                "diagnostic_confidence": 0.85,
                "supporting_findings": []
            }
        ],
        "uncertainty": {
            "status": "resolved",
            "abstain": False,
            "reason": None,
            "alternatives": []
        },
        "recommendations": [],
        "lineage": [],
        "metadata": {
            "trend_data": trend_data,
            "dimensions": dimensions,
            "events": events
        }
    }
    
    print("Sending payload to Visualizers API...")
    try:
        response = requests.post("http://localhost:8001/visualizations", json=payload)
        response.raise_for_status()
        
        specs = response.json()
        print(f"Success! Received {len(specs)} visualizer specs.")
        for spec in specs:
            print(f"- {spec['name']}: {spec['description']}")
            
        with open("frontend/Visualizers/sample_specs.json", "w") as f:
            json.dump(specs, f, indent=2)
            
        print("Saved specs to frontend/Visualizers/sample_specs.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
