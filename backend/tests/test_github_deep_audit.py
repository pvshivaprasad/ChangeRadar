"""Deep verification and audit test for ChangeRadar 1.0 GitHub Integration.
Directly exercises all security boundaries, encryption, webhooks, and isolation.
"""
import base64
import hashlib
import hmac
import json
import uuid
import pytest
from app.config import settings
from app.github.client import BOT_COMMENT_MARKER, GitHubClient
from app.github.service import GitHubService, SAFE_REPO_NAME_RE
from app.models import GitHubAccount, GitHubWebhookLog, Repository, User
from app.security import (
    _get_fernet_key,
    decrypt_secret,
    encrypt_secret,
    mask_token,
    verify_github_webhook_signature,
)


def test_token_encryption_and_missing_key_behavior():
    """Verify Fernet round-trip, key derivation, and production failure on missing key."""
    # 1. Standard round-trip
    token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    encrypted = encrypt_secret(token)
    assert encrypted != token
    assert decrypt_secret(encrypted) == token

    # 2. Key derivation from arbitrary string
    orig_key = settings.encryption_key
    try:
        settings.encryption_key = "my-custom-passphrase-not-base64"
        enc_custom = encrypt_secret(token)
        assert decrypt_secret(enc_custom) == token
    finally:
        settings.encryption_key = orig_key

    # 3. Corrupted ciphertext raises ValueError
    with pytest.raises(ValueError, match="Failed to decrypt"):
        decrypt_secret("not-a-valid-fernet-token")

    # 4. In production, missing encryption_key MUST raise ValueError
    orig_env = settings.environment
    orig_enc = settings.encryption_key
    try:
        settings.environment = "production"
        settings.encryption_key = None
        with pytest.raises(ValueError, match="ENCRYPTION_KEY must be configured in production"):
            encrypt_secret(token)
    finally:
        settings.environment = orig_env
        settings.encryption_key = orig_enc


def test_token_masking():
    """Verify that user-facing token strings never expose raw secrets."""
    assert mask_token("ghp_1234567890abcdef") == "ghp_****cdef"
    assert mask_token("short") == "********"
    assert mask_token("") == ""
    assert mask_token(None) == ""


def test_repo_name_and_path_traversal_guards():
    """Verify repo names and paths with path traversal attempts are blocked."""
    assert SAFE_REPO_NAME_RE.match("octocat/Hello-World")
    assert SAFE_REPO_NAME_RE.match("company_org/core.service")
    assert not SAFE_REPO_NAME_RE.match("../../etc/passwd")
    assert not SAFE_REPO_NAME_RE.match("owner/repo/extra")
    assert not SAFE_REPO_NAME_RE.match("owner;rm -rf /")


@pytest.mark.anyio
async def test_webhook_security_matrix(db_session):
    """Test HMAC validation, delivery deduplication, replayed events, and malformed JSON."""
    secret = "test_webhook_hmac_secret_456"
    orig_secret = settings.github_webhook_secret
    settings.github_webhook_secret = secret

    try:
        svc = GitHubService(db_session)
        payload = json.dumps({"action": "opened", "number": 42}).encode("utf-8")

        # 1. Valid HMAC signature
        valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        deliv1 = f"deliv_{uuid.uuid4().hex}"
        res1 = await svc.handle_webhook(
            delivery_id=deliv1,
            event_type="pull_request",
            payload_bytes=payload,
            signature_header=valid_sig,
        )
        assert res1["status"] in ("processed", "completed")

        # 2. Replayed webhook (duplicate delivery ID)
        res_replay = await svc.handle_webhook(
            delivery_id=deliv1,
            event_type="pull_request",
            payload_bytes=payload,
            signature_header=valid_sig,
        )
        assert res_replay["status"] == "duplicate_ignored"

        # 3. Invalid signature
        with pytest.raises(PermissionError, match="Invalid GitHub webhook signature"):
            await svc.handle_webhook(
                delivery_id=f"deliv_{uuid.uuid4().hex}",
                event_type="pull_request",
                payload_bytes=payload,
                signature_header="sha256=invalid_hex_digest_0000000000000000",
            )

        # 4. Missing signature header
        with pytest.raises(PermissionError, match="Invalid GitHub webhook signature"):
            await svc.handle_webhook(
                delivery_id=f"deliv_{uuid.uuid4().hex}",
                event_type="pull_request",
                payload_bytes=payload,
                signature_header=None,
            )

        # 5. Malformed payload bytes (unparseable JSON)
        bad_bytes = b"\x00\x01\x02\xffnot-valid-json{"
        bad_sig = "sha256=" + hmac.new(secret.encode("utf-8"), bad_bytes, hashlib.sha256).hexdigest()
        deliv_malformed = f"deliv_{uuid.uuid4().hex}"
        res_malformed = await svc.handle_webhook(
            delivery_id=deliv_malformed,
            event_type="unknown_event",
            payload_bytes=bad_bytes,
            signature_header=bad_sig,
        )
        assert res_malformed["status"] == "processed"
    finally:
        settings.github_webhook_secret = orig_secret


def test_user_tenant_isolation_on_github_account(db_session):
    """Verify that GitHub account tokens are isolated to the owning user."""
    u1 = User(email=f"u1_{uuid.uuid4().hex[:6]}@changeradar.dev", hashed_password="pw", name="User 1")
    u2 = User(email=f"u2_{uuid.uuid4().hex[:6]}@changeradar.dev", hashed_password="pw", name="User 2")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    # Directly persist an encrypted account for User 1
    acc1_row = GitHubAccount(
        user_id=u1.id,
        github_user_id="12345",
        github_username="octocat_user1",
        encrypted_access_token=encrypt_secret("ghp_u1secrettoken12345"),
        scopes="repo",
        account_type="pat",
    )
    db_session.add(acc1_row)
    db_session.commit()

    svc = GitHubService(db_session)

    # User 1 has account
    acc1 = svc.get_account(u1.id)
    assert acc1 is not None
    assert acc1.github_username == "octocat_user1"
    assert decrypt_secret(acc1.encrypted_access_token) == "ghp_u1secrettoken12345"

    # User 2 has NO account
    acc2 = svc.get_account(u2.id)
    assert acc2 is None

    # User 2 cannot disconnect User 1's account
    assert svc.disconnect_account(u2.id) is False
    assert svc.get_account(u1.id) is not None
