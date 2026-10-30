"""Tests for Historical Change Intelligence (Phase 2):
- Pattern aggregation across historical analyses
- Frequently modified modules and impacted components
- Recurring dependency paths and architectural hotspots
- Repeatedly recommended tests
- Analysis-to-analysis comparative intelligence (blast radius delta, test drift)
- Strict multi-tenant isolation on historical records
"""
import json
import uuid
import pytest
from app.historical.service import HistoricalIntelligenceService
from app.models import Analysis, Repository, User


def create_mock_analysis(
    db,
    user_id: int,
    repo_id: int,
    commit_sha: str,
    risk_level: str,
    risk_score: float,
    changed_files: list,
    changed_symbols: list,
    impacted_symbols: list,
    recommended_tests: list,
) -> Analysis:
    report = {
        "repo_path": "/fake/repo",
        "base_commit": "base_sha",
        "head_commit": commit_sha,
        "changed_files": changed_files,
        "changed_symbols": changed_symbols,
        "impacted_symbols": impacted_symbols,
        "recommended_tests": recommended_tests,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "graph_nodes_count": 20,
        "graph_edges_count": 25,
        "summary_text": f"Historical analysis for {commit_sha}",
    }
    analysis = Analysis(
        repository_id=repo_id,
        user_id=user_id,
        base_commit="base_sha",
        head_commit=commit_sha,
        status="completed",
        risk_level=risk_level,
        risk_score=risk_score,
        changed_files_count=len(changed_files),
        changed_symbols_count=len(changed_symbols),
        impacted_symbols_count=len(impacted_symbols),
        recommended_tests_count=len(recommended_tests),
        summary_text=f"Historical analysis for {commit_sha}",
        report_json=json.dumps(report),
        analysis_engine_version="1.0.0",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def test_empty_history(db_session):
    """When a repository has no analyses, service returns zeroed results without error."""
    svc = HistoricalIntelligenceService(db_session)
    res = svc.compute_change_patterns(repository_id=999999, user_id=999999)
    assert res["total_analyses"] == 0
    assert "Insufficient historical data" in res["message"]
    assert res["frequently_modified_modules"] == []
    assert res["hotspots"] == []


def test_historical_patterns_aggregation(db_session):
    """Verify aggregated metrics for modified modules, impacted components, and hotspots."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"hist_{uid}@changeradar.dev", hashed_password="pw", name="Historical User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    repo = Repository(name=f"hist-repo-{uid}", path=f"/test/path/{uid}", user_id=user.id)
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    # Commit 1: modified auth/service.py, elevated risk
    create_mock_analysis(
        db=db_session,
        user_id=user.id,
        repo_id=repo.id,
        commit_sha="c0011111",
        risk_level="elevated",
        risk_score=65.0,
        changed_files=["auth/service.py"],
        changed_symbols=[{"id": "auth.service.login", "name": "login"}],
        impacted_symbols=[
            {
                "symbol_id": "api.routes.login_endpoint",
                "symbol_name": "login_endpoint",
                "depth": 1,
                "path_from_change": ["auth.service.login", "api.routes.login_endpoint"],
            }
        ],
        recommended_tests=[{"test_file": "tests/test_auth.py", "test_symbol_id": "test_login"}],
    )

    # Commit 2: modified auth/service.py and checkout/pay.py, high risk
    create_mock_analysis(
        db=db_session,
        user_id=user.id,
        repo_id=repo.id,
        commit_sha="c0022222",
        risk_level="high",
        risk_score=85.0,
        changed_files=["auth/service.py", "checkout/pay.py"],
        changed_symbols=[
            {"id": "auth.service.verify_session", "name": "verify_session"},
            {"id": "checkout.pay.charge", "name": "charge"},
        ],
        impacted_symbols=[
            {
                "symbol_id": "api.routes.login_endpoint",
                "symbol_name": "login_endpoint",
                "depth": 1,
                "path_from_change": ["auth.service.verify_session", "api.routes.login_endpoint"],
            },
            {
                "symbol_id": "billing.worker.settle",
                "symbol_name": "settle",
                "depth": 2,
                "path_from_change": ["checkout.pay.charge", "billing.worker.settle"],
            },
        ],
        recommended_tests=[
            {"test_file": "tests/test_auth.py", "test_symbol_id": "test_verify_session"},
            {"test_file": "tests/test_checkout.py", "test_symbol_id": "test_charge"},
        ],
    )

    svc = HistoricalIntelligenceService(db_session)
    patterns = svc.compute_change_patterns(repository_id=repo.id, user_id=user.id)

    assert patterns["total_analyses"] == 2
    # Frequently modified: auth/service.py modified in 2 of 2 analyses (100.0%)
    top_mod = patterns["frequently_modified_modules"][0]
    assert top_mod["file_path"] == "auth/service.py"
    assert top_mod["change_count"] == 2
    assert top_mod["percentage"] == 100.0

    # Frequently impacted: api.routes.login_endpoint impacted in 2 of 2 analyses
    top_imp = patterns["frequently_impacted_components"][0]
    assert top_imp["symbol_id"] == "api.routes.login_endpoint"
    assert top_imp["impact_count"] == 2

    # Architectural hotspots: auth/service.py appeared in 2 elevated/high risk analyses
    assert len(patterns["hotspots"]) >= 1
    assert patterns["hotspots"][0]["file_path"] == "auth/service.py"
    assert patterns["hotspots"][0]["high_risk_occurrences"] == 2

    # Recurring paths
    paths = [p["path"] for p in patterns["recurring_paths"]]
    assert any("login_endpoint" in p for p in paths)

    # Risk trend
    assert len(patterns["risk_trend"]) == 2
    assert patterns["risk_trend"][0]["risk_score"] == 65.0
    assert patterns["risk_trend"][1]["risk_score"] == 85.0


def test_compare_analyses_intelligence(db_session):
    """Verify deep comparative diff between two analysis snapshots."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"comp_{uid}@changeradar.dev", hashed_password="pw", name="Comp User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    repo = Repository(name=f"comp-repo-{uid}", path=f"/test/path/{uid}", user_id=user.id)
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    a1 = create_mock_analysis(
        db=db_session,
        user_id=user.id,
        repo_id=repo.id,
        commit_sha="a1111111",
        risk_level="medium",
        risk_score=35.0,
        changed_files=["utils/helpers.py"],
        changed_symbols=[{"id": "utils.helpers.format_str"}],
        impacted_symbols=[{"symbol_id": "api.view.render"}],
        recommended_tests=[{"test_file": "tests/test_helpers.py"}],
    )

    a2 = create_mock_analysis(
        db=db_session,
        user_id=user.id,
        repo_id=repo.id,
        commit_sha="a2222222",
        risk_level="high",
        risk_score=75.0,
        changed_files=["utils/helpers.py", "core/db.py"],
        changed_symbols=[{"id": "utils.helpers.format_str"}, {"id": "core.db.connect"}],
        impacted_symbols=[{"symbol_id": "api.view.render"}, {"symbol_id": "services.data.query"}],
        recommended_tests=[{"test_file": "tests/test_helpers.py"}, {"test_file": "tests/test_db.py"}],
    )

    svc = HistoricalIntelligenceService(db_session)
    comp = svc.compare_analyses(a1.id, a2.id, user_id=user.id)

    assert comp["risk_score_delta"] == 40.0
    assert comp["impacted_count_delta"] == 1
    assert "services.data.query" in comp["newly_impacted_symbols"]
    assert "api.view.render" in comp["common_impacted_symbols"]
    assert "tests/test_db.py" in comp["newly_recommended_tests"]
    assert "tests/test_helpers.py" in comp["retained_tests"]


def test_historical_user_isolation(db_session):
    """Ensure users cannot inspect or compare historical analyses belonging to another user."""
    uid1 = uuid.uuid4().hex[:8]
    uid2 = uuid.uuid4().hex[:8]
    u1 = User(email=f"u1_{uid1}@changeradar.dev", hashed_password="pw", name="User 1")
    u2 = User(email=f"u2_{uid2}@changeradar.dev", hashed_password="pw", name="User 2")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    repo1 = Repository(name="r1", path="/p1", user_id=u1.id)
    db_session.add(repo1)
    db_session.commit()
    db_session.refresh(repo1)

    a1 = create_mock_analysis(
        db=db_session,
        user_id=u1.id,
        repo_id=repo1.id,
        commit_sha="u1comm",
        risk_level="low",
        risk_score=10.0,
        changed_files=["f.py"],
        changed_symbols=[],
        impacted_symbols=[],
        recommended_tests=[],
    )

    svc = HistoricalIntelligenceService(db_session)
    # User 2 tries to compute patterns on user 1's repo
    res = svc.compute_change_patterns(repository_id=repo1.id, user_id=u2.id)
    assert res["total_analyses"] == 0

    # User 2 tries to compare user 1's analyses
    with pytest.raises(ValueError):
        svc.compare_analyses(analysis_id_a=a1.id, analysis_id_b=a1.id, user_id=u2.id)
