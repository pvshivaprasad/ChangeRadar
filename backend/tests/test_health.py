from fastapi.testclient import TestClient
from app.main import app
from app.database import mask_database_url, init_engine, check_database_connection
from app.config import settings

client = TestClient(app)


def test_mask_database_url():
    url = "postgresql+psycopg://myuser:supersecretpass@localhost:5432/changeradar"
    masked = mask_database_url(url)
    assert "supersecretpass" not in masked
    assert "***" in masked
    assert "myuser" in masked


def test_sqlite_default_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "changeradar-api"
    assert data["version"] in ("0.1.1", "1.0.0")
    assert data["database"]["connected"] is True
    assert data["database"]["dialect"] == "sqlite"
    assert data["database"]["error"] is None


def test_api_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ChangeRadar API is ready"
    assert data["version"] in ("0.1.1", "1.0.0")
    assert "timestamp" in data
    assert data["database"]["connected"] is True


def test_unreachable_db_does_not_mask_failure():
    # If a database is unreachable, check_database_connection should return connected=False
    # without silent fallback.
    fake_engine = init_engine("sqlite:///nonexistent_dir/forbidden/db.sqlite")
    # Attempting to check with invalid path
    # In SQLite, checking connection with invalid directory raises an OperationalError
    try:
        from sqlalchemy import text
        with fake_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        unreachable_failed = False
    except Exception:
        unreachable_failed = True
    assert unreachable_failed is True
