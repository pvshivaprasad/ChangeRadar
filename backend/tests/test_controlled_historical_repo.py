"""Controlled Git repository test for Historical Change Intelligence.
Creates a real local Git repository with multiple commits, executes real AST change analyses,
persists records to database, and verifies pattern detection and comparative diffs.
"""
import os
import shutil
import subprocess
import uuid
import pytest
from sqlalchemy.orm import Session

from app.historical.service import HistoricalIntelligenceService
from app.models import Analysis, Repository, User
from app.scanner import (
    DependencyGraphEngine,
    GitDiffProcessor,
    ImpactAnalysisReport,
    RepositoryScanner,
    TestRecommendationEngine,
    run_impact_analysis,
)


@pytest.fixture
def controlled_git_repo(tmp_path):
    """Sets up a real local Git repository with 3 sequential commits modifying Python functions."""
    repo_dir = tmp_path / "controlled_repo"
    repo_dir.mkdir()

    # Git init
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Committer"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "committer@changeradar.dev"], cwd=repo_dir, check=True, capture_output=True)

    # 1. Base commit
    core_dir = repo_dir / "core"
    core_dir.mkdir()
    (core_dir / "__init__.py").write_text("", encoding="utf-8")
    (core_dir / "auth.py").write_text(
        "def verify_token(token: str) -> bool:\n    return len(token) > 0\n",
        encoding="utf-8",
    )

    api_dir = repo_dir / "api"
    api_dir.mkdir()
    (api_dir / "__init__.py").write_text("", encoding="utf-8")
    (api_dir / "routes.py").write_text(
        "from core.auth import verify_token\n\ndef login_endpoint(token: str):\n    return verify_token(token)\n",
        encoding="utf-8",
    )

    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_auth.py").write_text(
        "from core.auth import verify_token\n\ndef test_verify():\n    assert verify_token('valid')\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True, capture_output=True)
    c0 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True).stdout.strip()

    # 2. Second commit: Modify verify_token in core/auth.py
    (core_dir / "auth.py").write_text(
        "def verify_token(token: str) -> bool:\n    if not token:\n        return False\n    return len(token) >= 8\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "core/auth.py"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Harden verify_token validation"], cwd=repo_dir, check=True, capture_output=True)
    c1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True).stdout.strip()

    # 3. Third commit: Add hash_secret and update login_endpoint in api/routes.py
    (core_dir / "auth.py").write_text(
        "def verify_token(token: str) -> bool:\n    if not token:\n        return False\n    return len(token) >= 8\n\ndef hash_secret(secret: str) -> str:\n    return 'hashed_' + secret\n",
        encoding="utf-8",
    )
    (api_dir / "routes.py").write_text(
        "from core.auth import verify_token, hash_secret\n\ndef login_endpoint(token: str):\n    h = hash_secret(token)\n    return verify_token(h)\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Introduce hash_secret and route wiring"], cwd=repo_dir, check=True, capture_output=True)
    c2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True).stdout.strip()

    return {
        "repo_path": str(repo_dir),
        "commits": [c0, c1, c2],
    }


def test_controlled_historical_analysis_and_comparative_intelligence(controlled_git_repo, db_session):
    """
    Executes actual scanner & diff engines on a real multi-commit Git repository,
    persists real analysis records, and validates historical patterns and deltas.
    """
    repo_path = controlled_git_repo["repo_path"]
    c0, c1, c2 = controlled_git_repo["commits"]

    # 1. Setup User and Repository in DB
    user = User(email=f"hist_test_{uuid.uuid4().hex[:6]}@changeradar.dev", hashed_password="pw", name="Historical QA")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    repo_record = Repository(
        name="controlled-history-repo",
        path=repo_path,
        user_id=user.id,
        default_branch="master",
    )
    db_session.add(repo_record)
    db_session.commit()
    db_session.refresh(repo_record)

    # 2. Run Real Analysis 1: comparing c0 -> c1
    rep1 = run_impact_analysis(repo_path=repo_path, base_commit=c0, head_commit=c1)

    a1 = Analysis(
        user_id=user.id,
        repository_id=repo_record.id,
        repo_name=repo_record.name,
        repo_path=repo_path,
        base_commit=c0,
        head_commit=c1,
        status="completed",
        risk_level=rep1.risk_level,
        risk_score=rep1.risk_score,
        changed_files_count=len(rep1.changed_files),
        changed_symbols_count=len(rep1.changed_symbols),
        impacted_symbols_count=len(rep1.impacted_symbols),
        recommended_tests_count=len(rep1.recommended_tests),
        summary_text=rep1.summary_text,
        report_json=rep1.model_dump_json(),
        analysis_engine_version="1.0.0",
    )
    db_session.add(a1)
    db_session.commit()
    db_session.refresh(a1)

    # 3. Run Real Analysis 2: comparing c1 -> c2
    rep2 = run_impact_analysis(repo_path=repo_path, base_commit=c1, head_commit=c2)


    a2 = Analysis(
        user_id=user.id,
        repository_id=repo_record.id,
        repo_name=repo_record.name,
        repo_path=repo_path,
        base_commit=c1,
        head_commit=c2,
        status="completed",
        risk_level=rep2.risk_level,
        risk_score=rep2.risk_score,
        changed_files_count=len(rep2.changed_files),
        changed_symbols_count=len(rep2.changed_symbols),
        impacted_symbols_count=len(rep2.impacted_symbols),
        recommended_tests_count=len(rep2.recommended_tests),
        summary_text=rep2.summary_text,
        report_json=rep2.model_dump_json(),
        analysis_engine_version="1.0.0",
    )
    db_session.add(a2)
    db_session.commit()
    db_session.refresh(a2)

    # 4. Verify HistoricalIntelligenceService pattern calculations
    hist_svc = HistoricalIntelligenceService(db_session)
    patterns = hist_svc.compute_change_patterns(repo_record.id, user.id)

    assert patterns["total_analyses"] == 2
    # Verify core/auth.py was modified in 100% of the analyses
    frequently_modified = {m["file_path"]: m["change_count"] for m in patterns["frequently_modified_modules"]}
    assert "core/auth.py" in frequently_modified
    assert frequently_modified["core/auth.py"] == 2

    # Verify downstream impacted component was accurately identified
    impacted_symbols = {c["symbol_id"] for c in patterns["frequently_impacted_components"]}
    assert any("api.routes" in s for s in impacted_symbols)

    # Verify repeatedly recommended tests
    assert len(patterns["repeatedly_recommended_tests"]) >= 1

    # 5. Verify Comparative Intelligence Diff between Snapshot a1 and Snapshot a2
    comparison = hist_svc.compare_analyses(a1.id, a2.id, user_id=user.id)
    assert "risk_score_delta" in comparison
    assert "impacted_count_delta" in comparison
    assert isinstance(comparison["newly_impacted_symbols"], list)
    assert isinstance(comparison["retained_tests"], list)

    # 6. Verify behavior on empty repository (zero analyses)
    empty_patterns = hist_svc.compute_change_patterns(repository_id=999999, user_id=user.id)
    assert empty_patterns["total_analyses"] == 0
    assert "Insufficient historical data" in empty_patterns["message"]
    assert empty_patterns["frequently_modified_modules"] == []
