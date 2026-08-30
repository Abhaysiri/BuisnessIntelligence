import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta
from starlette.testclient import TestClient
from app.main import api


def test_telemetry_middleware_and_headers():
    client = TestClient(api)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "kpi-engine"}

    # Verify Hook 1 Telemetry response headers (§5.4, §8.1)
    assert "X-Trace-ID" in response.headers
    assert response.headers["X-Trace-ID"].startswith("tr-")
    assert "X-Latency-MS" in response.headers
    latency = float(response.headers["X-Latency-MS"])
    assert latency >= 0.0
    assert "X-Total-Cost-USD" in response.headers


def test_metrics_ingest_endpoint():
    client = TestClient(api)
    payload = {
        "tenant_id": "org_enterprise_1",
        "kpi_id": "net_revenue",
        "measurements": [
            {
                "tenant_id": "org_enterprise_1",
                "kpi_id": "net_revenue",
                "observed_at": "2026-08-30T12:00:00Z",
                "value": 150240.50,
                "dimensions": {"region": "US-East", "channel": "Direct"},
            },
            {
                "tenant_id": "org_enterprise_1",
                "kpi_id": "net_revenue",
                "observed_at": "2026-08-30T13:00:00Z",
                "value": 148900.00,
                "dimensions": {"region": "US-West", "channel": "Enterprise"},
            },
        ],
    }

    response = client.post("/api/v1/metrics/ingest", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["processed_count"] == 2
    assert data["quarantined_count"] == 0
    assert "X-Trace-ID" in response.headers


def test_quarantine_replay_endpoint():
    client = TestClient(api)
    payload = {
        "record_id": "rec_quarantine_987",
        "replayed_by": "operator_admin_1",
        "notes": "Remediated corrupted timestamp format from upstream",
    }

    response = client.post("/api/v1/quarantine/replay", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REPLAYED"
    assert data["record_id"] == "rec_quarantine_987"
    assert data["replayed_by"] == "operator_admin_1"
    assert data["admitted_to_gold"] is True


def test_timeseries_decompose_endpoint():
    client = TestClient(api)
    base_time = datetime(2026, 1, 1, 0, 0, 0)
    data_points = []
    for i in range(30):
        t_str = (base_time + timedelta(days=i)).isoformat()
        val = 100.0 + 2.0 * i + 10.0 * (1.0 if i % 7 in [0, 6] else 0.0)
        data_points.append({"timestamp": t_str, "value": val})

    payload = {
        "tenant_id": "tenant_test",
        "kpi_id": "test_kpi",
        "cadence": "daily",
        "data": data_points,
    }

    response = client.post("/api/v1/timeseries/decompose", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["tenant_id"] == "tenant_test"
    assert res["kpi_id"] == "test_kpi"
    assert res["observed_points"] == 30
    assert len(res["trend_data"]) == 30
    assert res["status"] == "SUCCESS"


if __name__ == "__main__":
    print("Running API Integration Tests...")
    test_telemetry_middleware_and_headers()
    test_metrics_ingest_endpoint()
    test_quarantine_replay_endpoint()
    test_timeseries_decompose_endpoint()
    print("All API integration tests passed successfully!")
