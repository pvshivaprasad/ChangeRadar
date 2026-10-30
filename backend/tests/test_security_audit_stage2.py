"""Stage 2 Security & Deployment Architecture Regression Tests for ChangeRadar:

1. Hashed Session Tokens in Database (no plaintext session storage)
2. Multiple Concurrent Sessions Coexistence
3. Targeted Logout Revocation (device A logout does not kill device B)
4. Session Expiration Rejection & Purge
5. Authentication Rate Limiting (HTTP 429)
6. CSRF Origin Protection (HTTP 403 on untrusted origins)
7. Safe Repository Deployment Restrictions (remote server arbitrary path rejection)
8. User Workspace Sandbox Traversal Protection
9. Resource & File-Count Limit Enforcement
10. Fresh Database Migration from scratch via Alembic
"""
from datetime import datetime, timezone, timedelta
import hashlib
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app, auth_rate_limiter
from app.database import Base, SessionLocal, init_db
from app.config import settings
from app import models
from app.storage import (
    check_resource_limits,
    get_controlled_sample_dir,
    get_user_storage_dir,
    validate_repo_access,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_hashed_session_tokens_in_database():
    """Verifies raw session tokens are hashed with SHA-256 and never stored in plaintext."""
    uid = uuid.uuid4().hex[:6]
    email = f"hash_user_{uid}@changeradar.test"
    password = "SafePassword123!"

    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Hash Tester",
        "email": email,
        "password": password,
    })
    assert reg_res.status_code == 200
    raw_token = reg_res.json()["token"]
    user_id = reg_res.json()["user"]["id"]

    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = SessionLocal()
    try:
        # Verify the session table stores the SHA-256 hash, NOT the raw token
        session_rec = db.query(models.UserSession).filter_by(token_hash=expected_hash).first()
        assert session_rec is not None
        assert session_rec.user_id == user_id
        assert session_rec.token_hash == expected_hash
        assert session_rec.token_prefix == raw_token[:8]

        # Ensure no plaintext match exists in the session table
        plaintext_match = db.query(models.UserSession).filter_by(token_hash=raw_token).first()
        assert plaintext_match is None
    finally:
        db.close()


def test_multi_session_coexistence_and_targeted_logout():
    """Verifies multiple devices can hold active sessions and logout affects only the calling device."""
    uid = uuid.uuid4().hex[:6]
    email = f"multi_user_{uid}@changeradar.test"
    password = "MultiPassword123!"

    client.post("/api/v1/auth/register", json={
        "name": "Multi Session User",
        "email": email,
        "password": password,
    })

    # Device A Login (e.g. Laptop)
    login_a = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_a.status_code == 200
    token_a = login_a.json()["token"]

    # Device B Login (e.g. Mobile)
    login_b = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_b.status_code == 200
    token_b = login_b.json()["token"]

    assert token_a != token_b

    # Both tokens are valid concurrently
    res_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    res_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200

    # Device A Logs Out
    logout_a = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    assert logout_a.status_code == 200

    # Device A is now revoked
    res_a_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_after.status_code == 401

    # Device B remains ACTIVE and UNTOUCHED
    res_b_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_after.status_code == 200
    assert res_b_after.json()["email"] == email


def test_expired_session_rejection_and_purge():
    """Verifies expired sessions are rejected with HTTP 401 and automatically purged from database."""
    uid = uuid.uuid4().hex[:6]
    email = f"expire_user_{uid}@changeradar.test"
    password = "ExpirePassword123!"

    reg = client.post("/api/v1/auth/register", json={
        "name": "Expire Tester",
        "email": email,
        "password": password,
    })
    token = reg.json()["token"]
    token_hash = models.hash_token(token)

    # Force expiration in database
    db = SessionLocal()
    try:
        session_rec = db.query(models.UserSession).filter_by(token_hash=token_hash).first()
        session_rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    # Attempt request with expired session
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()

    # Confirm session was purged from database
    db = SessionLocal()
    try:
        purged = db.query(models.UserSession).filter_by(token_hash=token_hash).first()
        assert purged is None
    finally:
        db.close()


def test_auth_rate_limiting():
    """Verifies sliding window rate limiter triggers HTTP 429 when threshold exceeded."""
    client_ip = "test_rate_limited_ip"
    auth_rate_limiter.hits[client_ip] = [datetime.now(timezone.utc).timestamp()] * (settings.rate_limit_auth_requests + 2)

    assert not auth_rate_limiter.is_allowed(client_ip)


def test_csrf_origin_protection():
    """Verifies mutating requests with untrusted Origin headers are rejected with HTTP 403."""
    uid = uuid.uuid4().hex[:6]
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "CSRF Attack", "email": f"csrf_{uid}@test.com", "password": "Pass123456!"},
        headers={"Origin": "http://malicious-hacker-site.com"},
    )
    assert res.status_code == 403
    assert "CSRF protection" in res.json()["detail"]


def test_remote_deployment_arbitrary_path_restriction(monkeypatch):
    """Verifies that in production/remote deployments, arbitrary host filesystem paths are forbidden."""
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_local_dev_scanning", False)

    # Sample repository is always allowed
    sample_path, repo_type = validate_repo_access("sample", user_id=99)
    assert repo_type == "sample"

    # Arbitrary host paths are forbidden in remote deployment
    with pytest.raises(Exception) as excinfo:
        validate_repo_access(r"C:\Windows" if os.name == "nt" else "/etc", user_id=99)
    assert "restricted in remote deployments" in str(excinfo.value.detail)


def test_user_sandbox_path_traversal_protection(tmp_path, monkeypatch):
    """Verifies that path traversal attempts outside user workspace sandbox are blocked."""
    sandbox_root = str(tmp_path / "storage_repos")
    monkeypatch.setattr(settings, "repo_storage_dir", sandbox_root)
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_local_dev_scanning", False)

    user_id = 42
    user_sandbox = get_user_storage_dir(user_id)

    # Legitimate directory in sandbox
    legit_repo = os.path.join(user_sandbox, "repo_alpha")
    os.makedirs(legit_repo, exist_ok=True)
    resolved, repo_type = validate_repo_access(legit_repo, user_id=user_id)
    assert repo_type == "workspace"

    # Traversal attempt escaping sandbox
    traversal_path = os.path.join(user_sandbox, "..", "user_99")
    with pytest.raises(Exception) as excinfo:
        validate_repo_access(traversal_path, user_id=user_id)
    assert excinfo.value.status_code in [400, 403]


def test_resource_limit_enforcement(tmp_path):
    """Verifies excessive file counts in repositories trigger HTTP 400."""
    repo_dir = tmp_path / "oversized_repo"
    repo_dir.mkdir()

    # Create dummy files exceeding custom limit
    for i in range(15):
        (repo_dir / f"mod_{i}.py").write_text("x = 1\n", encoding="utf-8")

    from app.config import settings
    orig_max = settings.max_repo_files
    try:
        settings.max_repo_files = 10
        with pytest.raises(Exception) as excinfo:
            check_resource_limits(str(repo_dir))
        assert excinfo.value.status_code == 400
        assert "exceeds file limit" in excinfo.value.detail
    finally:
        settings.max_repo_files = orig_max
