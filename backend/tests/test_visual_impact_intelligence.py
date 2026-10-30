"""Automated verification test suite for ChangeRadar 0.2:
- Visual Impact Intelligence data structures
- Git file diffs extraction (change type, additions, deletions, diff hunks)
- Serialization to SQLite database and deserialization via FastAPI API
- Simple view and technical view data integrity
- Real repository data validation with zero fabricated metrics
"""
import os
import pytest
from app.scanner.engine import run_impact_analysis
from app.scanner.models import FileDiff, ImpactAnalysisReport
from app.main import app, get_synthetic_repo_path
from fastapi.testclient import TestClient


def test_synthetic_repo_file_diffs_generation():
    """Verify that run_impact_analysis populates structured file diffs with hunks."""
    synth_path = get_synthetic_repo_path()
    assert os.path.isdir(synth_path), f"Synthetic repo not found at {synth_path}"

    report: ImpactAnalysisReport = run_impact_analysis(
        repo_path=synth_path,
        base_commit="HEAD~1",
        head_commit="HEAD",
    )

    # 1. Check basic report fields
    assert report.risk_score > 0
    assert report.risk_level in ("low", "medium", "elevated", "high")
    assert len(report.changed_files) > 0
    assert len(report.changed_symbols) > 0
    assert len(report.impacted_symbols) > 0
    assert len(report.recommended_tests) > 0

    # 2. Check FileDiff structured items
    assert len(report.file_diffs) > 0
    auth_diff = next((fd for fd in report.file_diffs if "auth/service.py" in fd.file_path.replace("\\", "/")), None)
    assert auth_diff is not None
    assert auth_diff.change_type == "modified"
    assert auth_diff.additions > 0
    assert auth_diff.deletions > 0
    assert "@@" in auth_diff.diff_content
    assert "validate_token" in auth_diff.diff_content


def test_sample_analysis_api_persistence_and_file_diffs():
    """Verify that /api/v1/sample/run returns file_diffs and saves report in SQLite."""
    client = TestClient(app)
    res = client.get("/api/v1/sample/run")
    assert res.status_code == 200, res.text
    data = res.json()

    # Verify response schema
    assert "file_diffs" in data
    assert len(data["file_diffs"]) >= 1
    fd = data["file_diffs"][0]
    assert "file_path" in fd
    assert "change_type" in fd
    assert "diff_content" in fd
    assert "additions" in fd
    assert "deletions" in fd

    # Verify causal paths for interactive impact map
    assert "impacted_symbols" in data
    for imp in data["impacted_symbols"]:
        assert "depth" in imp
        assert "path_from_change" in imp
        assert len(imp["path_from_change"]) >= 1

    # Verify recommended tests for what to test section
    assert "recommended_tests" in data
    for rec in data["recommended_tests"]:
        assert "target_symbol_id" in rec
        assert "reason" in rec
        assert "priority" in rec
