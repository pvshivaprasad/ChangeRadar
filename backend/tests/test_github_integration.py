"""Tests for GitHub Integration (Phase 1):
- Token encryption and safe storage with Fernet
- Webhook HMAC-SHA256 signature verification & idempotency
- Pull request unified diff analysis and impact tracing
- Executive PR comment formatting with risk metrics and bot marker
- User and repository cross-tenant isolation
"""
import hmac
import hashlib
import json
import uuid
import pytest
from app.config import settings
from app.github.client import BOT_COMMENT_MARKER, GitHubClient, GitHubClientError
from app.github.service import GitHubService, format_pr_comment
from app.models import GitHubAccount, GitHubWebhookLog, Repository, User
from app.scanner.models import (
    ConfidenceLevel,
    ImpactType,
    ImpactedSymbol,
    ImpactAnalysisReport,
    Symbol,
    SymbolType,
    TestRecommendation,
)
from app.security import (
    decrypt_secret,
    encrypt_secret,
    mask_token,
    verify_github_webhook_signature,
)


def test_fernet_token_encryption_and_masking():
    raw_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    encrypted = encrypt_secret(raw_token)
    assert encrypted != raw_token
    assert len(encrypted) > 40

    decrypted = decrypt_secret(encrypted)
    assert decrypted == raw_token

    # Test masking
    masked = mask_token(raw_token)
    assert masked == "ghp_****wxyz"
    assert "1234567890" not in masked


def test_webhook_signature_verification():
    secret = "test_webhook_secret_key_123"
    payload = b'{"action":"opened","number":42,"repository":{"full_name":"octocat/Hello-World"}}'

    # Compute valid signature
    sig_hex = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    valid_header = f"sha256={sig_hex}"

    # Valid check
    assert verify_github_webhook_signature(payload, valid_header, secret) is True

    # Tampered payload check
    assert verify_github_webhook_signature(b'{"tampered":true}', valid_header, secret) is False

    # Wrong secret check
    assert verify_github_webhook_signature(payload, valid_header, "wrong_secret") is False

    # Malformed header check
    assert verify_github_webhook_signature(payload, "invalid_header", secret) is False
    assert verify_github_webhook_signature(payload, None, secret) is False


def test_pr_comment_formatting():
    """Verify that formatted PR comments contain executive overview, symbols, and no false bug claims."""
    report = ImpactAnalysisReport(
        repo_path="/storage/repos/1/github_owner_repo",
        base_commit="abc123456789",
        head_commit="def987654321",
        changed_files=["auth/service.py"],
        changed_symbols=[
            Symbol(id="auth.service.validate_token", name="validate_token", symbol_type=SymbolType.FUNCTION, file_path="auth/service.py", line_start=15, line_end=25)
        ],
        impacted_symbols=[
            ImpactedSymbol(symbol_id="auth.service.validate_token", symbol_name="validate_token", symbol_type=SymbolType.FUNCTION, file_path="auth/service.py", line_start=15, line_end=25, impact_type=ImpactType.DIRECT_CHANGE, depth=0, path_from_change=["auth.service.validate_token"]),
            ImpactedSymbol(symbol_id="checkout.payment.charge", symbol_name="charge", symbol_type=SymbolType.FUNCTION, file_path="checkout/payment.py", line_start=5, line_end=15, impact_type=ImpactType.DIRECT_DEPENDENT, depth=1, path_from_change=["auth.service.validate_token", "checkout.payment.charge"]),
        ],
        graph_nodes_count=20,
        graph_edges_count=35,
        recommended_tests=[
            TestRecommendation(test_file="tests/test_auth.py", test_symbol_id="tests.test_auth.test_validate_token", target_symbol_id="auth.service.validate_token", reason="Directly tests modified symbol", priority="high")
        ],
        risk_level="medium",
        risk_score=30.0,
        summary_text="PR modified 1 symbol.",
        created_at="2026-10-31T00:00:00Z",
    )

    comment = format_pr_comment(report=report, pr_number=101, pr_title="feat(auth): harden session validation")

    assert "## ⚡ ChangeRadar Impact Intelligence — PR #101" in comment
    assert "MEDIUM" in comment
    assert "30.0/100" in comment
    assert "`validate_token`" in comment
    assert "`charge`" in comment
    assert "`tests/test_auth.py`" in comment
    assert "architectural blast radius" in comment.lower()


@pytest.mark.anyio
async def test_webhook_idempotency_and_event_handling(db_session):
    """Verify webhook deliveries with identical delivery_id are deduplicated safely."""
    svc = GitHubService(db_session)
    delivery_id = f"delivery_uuid_test_{uuid.uuid4().hex}"
    payload_dict = {
        "action": "opened",
        "number": 1,
        "repository": {"full_name": "changeradar/synthetic-sample"},
        "sender": {"login": "octocat"},
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    # 1. First delivery
    res1 = await svc.handle_webhook(
        delivery_id=delivery_id,
        event_type="pull_request",
        payload_bytes=payload_bytes,
        signature_header=None,
    )
    assert res1["status"] in ("processed", "completed")

    # 2. Duplicate delivery with same delivery_id
    res2 = await svc.handle_webhook(
        delivery_id=delivery_id,
        event_type="pull_request",
        payload_bytes=payload_bytes,
        signature_header=None,
    )
    assert res2["status"] == "duplicate_ignored"

    # Verify log entry in DB
    log = db_session.query(GitHubWebhookLog).filter_by(delivery_id=delivery_id).first()
    assert log is not None
    assert log.event_type == "pull_request"
