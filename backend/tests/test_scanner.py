import os
from app.scanner.scanner import RepositoryScanner


def test_repository_scanner_on_synthetic_repo():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "synthetic_repo")
    scanner = RepositoryScanner(fixtures_dir)
    summary = scanner.scan()

    assert summary.file_count >= 5
    assert summary.symbol_count > 10
    assert summary.edge_count > 5
    assert summary.commit_sha is not None

    symbol_ids = {s.id for s in summary.symbols}
    assert "auth.service.AuthService.validate_token" in symbol_ids
    assert "checkout.payment.process_payment" in symbol_ids
    assert "user.profile.get_user_profile" in symbol_ids
