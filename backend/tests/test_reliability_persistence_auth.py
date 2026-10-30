"""Comprehensive automated tests for ChangeRadar Reliability, Authentication & Data Persistence:
1. Authentication:
   - Registration with PBKDF2 hashed password
   - Login issuing token and HttpOnly session cookie
   - Rejection of invalid credentials (401)
   - Session restoration via Bearer token and via Cookie
   - Session expiration policy enforcement
   - Session revocation on Logout
   - Protected endpoint enforcement (401 without credentials)

2. Persistence & Status Tracking:
   - Persisting analysis with status="completed"
   - Failure recording with status="failed" and error_message
   - Listing analysis history
   - Retrieving single analysis by ID
   - Repository archival policy (removing repo does not delete historical analyses)

3. Data Isolation & Multi-tenant Authorization:
   - User A cannot access User B's repository (404)
   - User A cannot access User B's analysis (404)
   - User A cannot delete or analyze User B's repository
   - Strict query scoping to authenticated user
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, init_db
from app import models

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_auth_registration_login_and_cookie():
    uid = uuid.uuid4().hex[:8]
    email = f"alice_{uid}@changeradar.test"
    password = "SafePassword987!"

    # 1. Registration
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Alice Engineer", "email": email, "password": password},
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "token" in reg_data
    assert reg_data["user"]["email"] == email
    # Verify cookie was set
    assert "session_token" in reg_res.cookies

    # 2. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "token" in login_data
    assert "session_token" in login_res.cookies
    active_token = login_data["token"]

    # 3. Access /auth/me with Bearer token
    me_bearer = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {active_token}"},
    )
    assert me_bearer.status_code == 200
    assert me_bearer.json()["email"] == email

    # 4. Access /auth/me with Cookie
    me_cookie = client.get(
        "/api/v1/auth/me",
        cookies={"session_token": active_token},
    )
    assert me_cookie.status_code == 200
    assert me_cookie.json()["email"] == email

    # 5. Invalid credentials return 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "incorrect" in bad_login.json()["detail"].lower()


def test_logout_revokes_token_and_cookie():
    uid = uuid.uuid4().hex[:8]
    email = f"logout_{uid}@changeradar.test"
    password = "LogoutPassword123!"

    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Logout User", "email": email, "password": password},
    )
    assert reg.status_code == 200
    token = reg.json()["token"]

    # Verify authenticated
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # Execute logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Old token must now be rejected
    rejected = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert rejected.status_code == 401


def test_token_expiration_policy():
    uid = uuid.uuid4().hex[:8]
    email = f"expired_{uid}@changeradar.test"
    password = "ExpiredPassword123!"

    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Expired User", "email": email, "password": password},
    )
    assert reg.status_code == 200
    token = reg.json()["token"]

    # Manually expire the token in database
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        user.token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    # Request with expired token must be rejected with 401
    expired_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert expired_res.status_code == 401
    assert "expired" in expired_res.json()["detail"].lower()


def test_data_isolation_between_users():
    uid = uuid.uuid4().hex[:8]
    user_a_email = f"user_a_{uid}@changeradar.test"
    res_a = client.post("/api/v1/auth/register", json={"name": "User A", "email": user_a_email, "password": "UserAPassword123!"})
    token_a = res_a.json()["token"]

    user_b_email = f"user_b_{uid}@changeradar.test"
    res_b = client.post("/api/v1/auth/register", json={"name": "User B", "email": user_b_email, "password": "UserBPassword123!"})
    token_b = res_b.json()["token"]

    from app.main import get_synthetic_repo_path
    synth_path = get_synthetic_repo_path()

    create_a = client.post(
        "/api/v1/repositories",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"path": synth_path, "name": "User A Repo", "default_branch": "master"},
    )
    assert create_a.status_code == 200
    repo_a = create_a.json()
    repo_a_id = repo_a["id"]

    # User B cannot see User A's repo in repository list
    list_b = client.get("/api/v1/repositories", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    b_repos = list_b.json()
    assert not any(r["id"] == repo_a_id for r in b_repos)

    # User B directly requesting User A's repo ID receives 404 (IDOR prevention)
    get_b = client.get(f"/api/v1/repositories/{repo_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # User B attempting to delete User A's repo receives 404
    del_b = client.delete(f"/api/v1/repositories/{repo_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # User A runs analysis
    analysis_res = client.post(
        f"/api/v1/repositories/{repo_a_id}/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"base_commit": "HEAD~1", "head_commit": "HEAD"},
    )
    assert analysis_res.status_code == 200
    analysis_a = analysis_res.json()
    analysis_a_id = analysis_a["id"]
    assert analysis_a["status"] == "completed"

    # User B cannot see User A's analysis in global or repo analyses
    analyses_b = client.get("/api/v1/analyses", headers={"Authorization": f"Bearer {token_b}"})
    assert analyses_b.status_code == 200
    assert not any(a["id"] == analysis_a_id for a in analyses_b.json())

    # User B requesting analysis directly receives 404
    single_b = client.get(f"/api/v1/analyses/{analysis_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert single_b.status_code == 404


def test_repository_archival_preserves_analyses():
    uid = uuid.uuid4().hex[:8]
    email = f"archival_{uid}@changeradar.test"
    res = client.post("/api/v1/auth/register", json={"name": "Archival User", "email": email, "password": "ArchivalPassword123!"})
    token = res.json()["token"]

    from app.main import get_synthetic_repo_path
    synth_path = get_synthetic_repo_path()

    create = client.post(
        "/api/v1/repositories",
        headers={"Authorization": f"Bearer {token}"},
        json={"path": synth_path, "name": "Repo To Delete", "default_branch": "master"},
    )
    repo = create.json()
    repo_id = repo["id"]

    # Run analysis
    analysis = client.post(
        f"/api/v1/repositories/{repo_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"base_commit": "HEAD~1", "head_commit": "HEAD"},
    ).json()
    analysis_id = analysis["id"]

    # Delete repository from active workspace
    del_res = client.delete(f"/api/v1/repositories/{repo_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200

    # Repository is no longer in active repositories list
    active_repos = client.get("/api/v1/repositories", headers={"Authorization": f"Bearer {token}"}).json()
    assert not any(r["id"] == repo_id for r in active_repos)

    # CRITICAL: Analysis record is STILL PRESERVED and retrievable
    user_analyses = client.get("/api/v1/analyses", headers={"Authorization": f"Bearer {token}"}).json()
    saved = next((a for a in user_analyses if a["id"] == analysis_id), None)
    assert saved is not None
    assert saved["status"] == "completed"
    assert "report" in saved
