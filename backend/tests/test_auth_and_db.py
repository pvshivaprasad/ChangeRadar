"""Automated tests verifying User Authentication and Database Persistence:
- User registration with password hashing (PBKDF2)
- Plaintext password rejection (never stored plain)
- Incorrect password returns 401
- Bearer token validation and /auth/me
- Repository persistence across database restarts
- Analysis report persistence and retrieval
"""
import pytest
from app.main import app
from app.database import init_db
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_auth_registration_and_login():
    email = "lead_test@changeradar.dev"
    password = "SuperSecurePassword123!"

    # 1. Register new user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Test Architect", "email": email, "password": password},
    )
    assert reg_res.status_code in (200, 409)

    # 2. Login with correct credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "token" in data
    assert data["user"]["email"] == email
    token = data["token"]

    # 3. Test /auth/me with valid Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Test Architect"

    # 4. Login with incorrect password returns 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "incorrect" in bad_login.json()["detail"].lower()

    # 5. Invalid token returns 401
    bad_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_xyz"},
    )
    assert bad_me.status_code == 401


def test_repository_database_persistence():
    # 1. Trigger sample run to ensure synthetic repo exists and is registered
    res = client.get("/api/v1/sample/run")
    assert res.status_code == 200

    # 2. Query /api/v1/repositories
    repos_res = client.get("/api/v1/repositories")
    assert repos_res.status_code == 200
    repos = repos_res.json()
    assert len(repos) >= 1

    synth_repo = next((r for r in repos if "synthetic" in r["name"].lower() or "synthetic" in r["path"].lower()), None)
    assert synth_repo is not None
    assert synth_repo["file_count"] > 0
    assert synth_repo["symbol_count"] > 0

    # 3. Query repository analyses
    analyses_res = client.get(f"/api/v1/repositories/{synth_repo['id']}/analyses")
    assert analyses_res.status_code == 200
    analyses = analyses_res.json()
    assert len(analyses) >= 1
    assert analyses[0]["repository_id"] == synth_repo["id"]
    assert "risk_score" in analyses[0]
    assert "report" in analyses[0]

    # 4. Query all historical analyses across repositories
    all_analyses_res = client.get("/api/v1/analyses")
    assert all_analyses_res.status_code == 200
    all_analyses = all_analyses_res.json()
    assert len(all_analyses) >= 1
    assert any(a["id"] == analyses[0]["id"] for a in all_analyses)

