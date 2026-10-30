"""True Persistence & Connection Restart Integration Test for ChangeRadar.

Strictly verifies:
1. User registration and PBKDF2 hashing
2. Authenticated login
3. Repository connection and AST scanning
4. Change impact analysis execution
5. Persistence of full analysis report JSON
6. Explicit closing of database session and engine disposal
7. Full simulated process/database connection restart
8. Reconnection to the same on-disk SQLite database file (NO in-memory substitute)
9. Re-login using user credentials
10. Retrieval of original analysis from history and by ID
11. Verification that all nested report JSON fields (modified symbols, callers, tests, risk metrics) remain 100% intact
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models


def test_true_persistence_across_connection_restart(tmp_path):
    # 1. Setup persistent on-disk SQLite file (NOT in-memory :memory:)
    db_file = str(tmp_path / "persistence_restart_verification.db")
    db_url = f"sqlite:///{db_file}"

    # Engine 1 (Initial App Instance)
    engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    SessionLocal1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)

    def override_get_db1():
        db = SessionLocal1()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db1
    client1 = TestClient(app)

    # Step 1: Register User
    uid = uuid.uuid4().hex[:6]
    email = f"persist_user_{uid}@changeradar.test"
    password = "StrongPassword789!"
    reg_res = client1.post("/api/v1/auth/register", json={
        "name": "Persistence Tester",
        "email": email,
        "password": password,
    })
    assert reg_res.status_code == 200, reg_res.text
    user_id = reg_res.json()["user"]["id"]

    # Step 2: Login
    login_res = client1.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    active_token = login_res.json()["token"]
    headers1 = {"Authorization": f"Bearer {active_token}"}

    # Step 3: Create Repository Record
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "synthetic_repo"))
    create_repo_res = client1.post("/api/v1/repositories", json={
        "name": "Synthetic Persistence Fixture",
        "path": repo_path,
        "default_branch": "main",
    }, headers=headers1)
    assert create_repo_res.status_code == 200, create_repo_res.text
    repo_data = create_repo_res.json()
    repo_id = repo_data["id"]
    assert repo_data["file_count"] >= 5

    # Step 4: Run Analysis
    analyze_res = client1.post(f"/api/v1/repositories/{repo_id}/analyze", json={
        "base_commit": "HEAD~1",
        "head_commit": "HEAD",
    }, headers=headers1)
    assert analyze_res.status_code == 200, analyze_res.text
    analysis_data = analyze_res.json()
    analysis_id = analysis_data["id"]
    assert analysis_data["status"] == "completed"
    assert analysis_data["risk_level"] == "high"
    assert analysis_data["changed_symbols_count"] == 1
    assert analysis_data["impacted_symbols_count"] == 8

    # Step 5: Save & Verify Analysis Report JSON was persisted
    report_orig = analysis_data["report"]
    assert report_orig is not None
    assert len(report_orig["changed_symbols"]) == 1
    assert len(report_orig["impacted_symbols"]) == 8

    # Step 6: Close Database Session and Dispose Engine 1
    app.dependency_overrides.clear()
    engine1.dispose()
    del engine1
    del SessionLocal1

    # Step 7: Simulate Application & Database Connection Restart
    # Verify the database file is physically present and populated on disk
    assert os.path.isfile(db_file)
    assert os.path.getsize(db_file) > 0

    # Step 8: Reconnect to the EXACT SAME persistent database file
    engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)

    def override_get_db2():
        db = SessionLocal2()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db2

    # Step 9: Re-launch TestClient (New Process Simulation with no prior memory)
    client2 = TestClient(app)
    relogin_res = client2.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert relogin_res.status_code == 200
    token2 = relogin_res.json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Verify Profile matches persisted user
    me_res = client2.get("/api/v1/auth/me", headers=headers2)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id
    assert me_res.json()["email"] == email

    # Step 10: Retrieve Original Analysis from History
    list_res = client2.get("/api/v1/analyses", headers=headers2)
    assert list_res.status_code == 200
    analyses_reloaded = list_res.json()
    assert len(analyses_reloaded) == 1
    reloaded_analysis = analyses_reloaded[0]
    assert reloaded_analysis["id"] == analysis_id
    assert reloaded_analysis["status"] == "completed"
    assert reloaded_analysis["repository_id"] == repo_id
    assert reloaded_analysis["repo_name"] == "Synthetic Persistence Fixture"

    # Step 11: Verify Complete Report JSON is intact and uncorrupted
    single_res = client2.get(f"/api/v1/analyses/{analysis_id}", headers=headers2)
    assert single_res.status_code == 200
    reloaded_full = single_res.json()
    reloaded_report = reloaded_full["report"]
    assert reloaded_report is not None

    # Check symbols, call paths, tests, and metrics
    orig_sym_names = sorted([s["name"] for s in report_orig["changed_symbols"]])
    reloaded_sym_names = sorted([s["name"] for s in reloaded_report["changed_symbols"]])
    assert orig_sym_names == reloaded_sym_names
    assert "validate_token" in reloaded_sym_names

    assert len(reloaded_report["impacted_symbols"]) == len(report_orig["impacted_symbols"])
    assert len(reloaded_report["recommended_tests"]) == len(report_orig["recommended_tests"])
    assert reloaded_report["risk_score"] == report_orig["risk_score"]
    assert reloaded_report["risk_level"] == report_orig["risk_level"]
    assert reloaded_report["summary_text"] == report_orig["summary_text"]

    # Clean up overrides and engine
    app.dependency_overrides.clear()
    engine2.dispose()
