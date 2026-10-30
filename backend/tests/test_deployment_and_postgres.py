"""Tests for Production Deployment, PostgreSQL Compatibility & Background Job Manager (Phase 3):
- PostgreSQL DDL compilation for all SQLAlchemy models (dual-dialect verification)
- /health and /ready production probe endpoints
- In-process background job lifecycle, concurrency limits, and deduplication
"""
import asyncio
import json
import uuid
import pytest
from sqlalchemy import create_mock_engine
from app.database import Base
from app.jobs.manager import BackgroundJobManager
from app.models import BackgroundJob, User


def test_postgresql_ddl_compilation():
    """Verify that all SQLAlchemy ORM models compile into valid PostgreSQL DDL without errors."""
    emitted_ddl = []

    def mock_executor(sql, *multiparams, **params):
        emitted_ddl.append(str(sql.compile(dialect=mock_engine.dialect)))

    mock_engine = create_mock_engine("postgresql+psycopg2://", executor=mock_executor)
    Base.metadata.create_all(mock_engine)

    full_ddl_text = "\n".join(emitted_ddl).lower()

    # Verify all expected tables are generated in PostgreSQL dialect
    expected_tables = [
        "users",
        "user_sessions",
        "repositories",
        "analyses",
        "github_accounts",
        "github_webhook_logs",
        "background_jobs",
    ]
    for table in expected_tables:
        assert f"create table {table}" in full_ddl_text, f"Table {table} missing from PostgreSQL DDL"

    # Verify PostgreSQL specific types and constraints are properly compiled
    assert "references users (id)" in full_ddl_text
    assert "references repositories (id)" in full_ddl_text
    assert "timestamp" in full_ddl_text

    # Verify all Boolean columns use PostgreSQL-compatible DEFAULT false (never DEFAULT 0)
    assert "boolean default 0" not in full_ddl_text, "Found invalid integer default for boolean column in PostgreSQL DDL"
    assert "is_archived boolean default false" in full_ddl_text
    assert "is_private boolean default false" in full_ddl_text
    assert "is_github_pr boolean default false" in full_ddl_text


def test_postgresql_and_sqlite_boolean_defaults_compatibility():
    """Verify that boolean server defaults compile to native representations in both PostgreSQL and SQLite."""
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql, sqlite

    col = sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False)
    table = sa.Table("test_repo", sa.MetaData(), col)

    pg_sql = str(sa.schema.CreateTable(table).compile(dialect=postgresql.dialect())).lower()
    sqlite_sql = str(sa.schema.CreateTable(table).compile(dialect=sqlite.dialect())).lower()

    # PostgreSQL must compile to 'boolean default false' (not default 0)
    assert "is_archived boolean default false not null" in pg_sql
    assert "default 0" not in pg_sql

    # SQLite must compile to 'boolean default 0' (valid SQLite boolean integer)
    assert "is_archived boolean default 0 not null" in sqlite_sql


def test_fresh_database_alembic_upgrade_downgrade_cycle(tmp_path):
    """Verify that Alembic migrations can initialize a fresh database from scratch, downgrade to base, and upgrade back to head."""
    import os
    from alembic.config import Config
    from alembic import command

    db_file = os.path.join(tmp_path, "fresh_migration_test.db")
    db_url = f"sqlite:///{db_file}"

    # Backup DATABASE_URL env var
    old_db_url = os.environ.get("DATABASE_URL")
    try:
        os.environ["DATABASE_URL"] = db_url

        cfg = Config("backend/alembic.ini")
        cfg.set_main_option("script_location", "backend/alembic")

        # 1. Fresh upgrade to head
        command.upgrade(cfg, "head")

        # 2. Downgrade all the way to base
        command.downgrade(cfg, "base")

        # 3. Re-upgrade back to head
        command.upgrade(cfg, "head")
    finally:
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
        else:
            os.environ.pop("DATABASE_URL", None)



def test_health_endpoint(client):
    """Verify /health liveness probe returns 200 and version info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ok")
    assert data["service"] == "changeradar-api"
    assert data["version"] == "1.0.0"


def test_ready_endpoint(client):
    """Verify /ready readiness probe validates database connectivity."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data


@pytest.mark.anyio
async def test_background_job_execution_lifecycle(db_session):
    """Verify full job lifecycle: creation -> execution -> completion with result."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"job_{uid}@changeradar.dev", hashed_password="pw", name="Job User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    params = {"repo_id": 42, "branch": "test-branch"}
    job = BackgroundJobManager.create_job(
        db=db_session,
        user_id=user.id,
        job_type="change_analysis",
        params=params,
    )
    assert job.status == "queued"
    assert job.progress_percent == 0

    # Test duplicate job suppression (idempotency)
    dup_job = BackgroundJobManager.create_job(
        db=db_session,
        user_id=user.id,
        job_type="change_analysis",
        params=params,
    )
    assert dup_job.id == job.id

    # Execute coroutine
    async def sample_task(repo_id: int, branch: str):
        await asyncio.sleep(0.01)
        return {"status": "success", "repo_id": repo_id, "branch": branch, "risk": "low"}

    await BackgroundJobManager._execute_coroutine(job.id, sample_task, **params)

    # Re-query
    db_session.expire_all()
    finished_job = db_session.query(BackgroundJob).filter_by(id=job.id).first()
    assert finished_job.status == "completed"
    assert finished_job.progress_percent == 100
    assert finished_job.completed_at is not None

    res = json.loads(finished_job.result_json)
    assert res["status"] == "success"
    assert res["repo_id"] == 42


def test_background_job_concurrency_throttling(db_session):
    """Verify max 3 concurrent active jobs per user enforcement."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"throttle_{uid}@changeradar.dev", hashed_password="pw", name="Throttle User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create 3 active queued jobs
    j1 = BackgroundJobManager.create_job(db_session, user.id, "job1", {"slot": 1})
    j2 = BackgroundJobManager.create_job(db_session, user.id, "job2", {"slot": 2})
    j3 = BackgroundJobManager.create_job(db_session, user.id, "job3", {"slot": 3})

    assert j1.status == "queued"
    assert j2.status == "queued"
    assert j3.status == "queued"

    # 4th concurrent job must be rejected with concurrency limit exception
    with pytest.raises(RuntimeError) as exc_info:
        BackgroundJobManager.create_job(db_session, user.id, "job4", {"slot": 4})

    assert "Maximum concurrent analysis jobs limit reached (3)" in str(exc_info.value)
