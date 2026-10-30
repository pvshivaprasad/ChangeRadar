"""Automated test suite verifying API path safety, abuse prevention, and error handling:
- System root / drive root directory rejection (HTTP 403)
- Windows / Linux system directory rejection (HTTP 403)
- Non-existent path rejection (HTTP 400)
- Empty path rejection (HTTP 400)
- Invalid git revision format handling
"""
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_reject_system_directory_scan():
    # Attempting to scan C:\Windows or /etc must be forbidden
    res = client.post("/api/v1/scan", json={"repo_path": "C:\\Windows"})
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()


def test_reject_drive_root_scan():
    # Attempting to scan drive root directly must be forbidden
    res = client.post("/api/v1/scan", json={"repo_path": "C:\\"})
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()


def test_reject_nonexistent_directory_scan():
    res = client.post("/api/v1/scan", json={"repo_path": "C:\\nonexistent_dir_12345_xyz"})
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"].lower()


def test_reject_empty_path_scan():
    res = client.post("/api/v1/scan", json={"repo_path": "   "})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_reject_system_directory_analyze():
    res = client.post(
        "/api/v1/analyze",
        json={"repo_path": "C:\\Windows", "base_commit": "HEAD~1", "head_commit": "HEAD"},
    )
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()


def test_reject_invalid_git_revision_analyze(tmp_path):
    # Valid directory but dangerous git ref
    res = client.post(
        "/api/v1/analyze",
        json={
            "repo_path": str(tmp_path),
            "base_commit": "--output=/tmp/evil",
            "head_commit": "HEAD",
        },
    )
    assert res.status_code == 400
    assert "invalid base commit" in res.json()["detail"].lower()
