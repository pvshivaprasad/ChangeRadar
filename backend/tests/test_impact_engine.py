import os
from app.scanner.engine import run_impact_analysis
from app.scanner.git_diff import GitDiffProcessor
from app.scanner.scanner import RepositoryScanner


def test_full_impact_analysis_on_synthetic_repo():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "synthetic_repo")

    # Run analysis comparing HEAD~1 with HEAD
    report = run_impact_analysis(
        repo_path=fixtures_dir,
        base_commit="HEAD~1",
        head_commit="HEAD",
    )

    assert len(report.changed_files) == 1
    assert "auth/service.py" in report.changed_files[0].replace("\\", "/")

    # Changed symbol should be AuthService.validate_token
    changed_ids = [s.id for s in report.changed_symbols]
    assert "auth.service.AuthService.validate_token" in changed_ids

    # Blast radius should identify both callers
    impacted_ids = [s.symbol_id for s in report.impacted_symbols]
    assert "auth.service.AuthService.validate_token" in impacted_ids
    assert "checkout.payment.process_payment" in impacted_ids
    assert "user.profile.get_user_profile" in impacted_ids

    # Test recommendations must include tests for auth and downstream callers
    rec_files = [r.test_file.replace("\\", "/") for r in report.recommended_tests]
    assert any("test_auth.py" in f for f in rec_files)
    assert any("test_payment.py" in f for f in rec_files) or any("test_profile.py" in f for f in rec_files)

    assert report.risk_level in ("low", "medium", "elevated", "high")
    assert report.risk_score > 0.0
