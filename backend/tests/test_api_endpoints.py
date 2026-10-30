from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_sample_scan_endpoint():
    res = client.get("/api/v1/sample/scan")
    assert res.status_code == 200
    data = res.json()
    assert data["file_count"] >= 5
    assert data["symbol_count"] > 10
    assert len(data["symbols"]) > 0


def test_api_sample_run_endpoint():
    res = client.get("/api/v1/sample/run")
    assert res.status_code == 200
    data = res.json()
    changed_names = {s["name"] for s in data["changed_symbols"]}
    assert "validate_token" in changed_names
    assert len(data["impacted_symbols"]) >= 3
    assert len(data["recommended_tests"]) >= 1
    assert "summary_text" in data
