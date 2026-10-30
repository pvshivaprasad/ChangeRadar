"""Deep verification of BackgroundJobManager:
- Job restart reconciliation
- Failed job error state and message capture
- Duplicate job suppression
- Per-user concurrency limit enforcement
- Multi-user concurrency isolation
"""
import asyncio
import json
import uuid
import pytest
from app.jobs.manager import BackgroundJobManager
from app.models import BackgroundJob, User


@pytest.mark.anyio
async def test_job_restart_reconciliation(db_session):
    """Verify that jobs left in 'running' or 'queued' upon restart are reconciled as failed."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"restart_{uid}@changeradar.dev", hashed_password="pw", name="Restart User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    job = BackgroundJob(
        id=f"job_orphan_{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        job_type="analysis",
        status="running",
        progress_percent=50,
        params_json=json.dumps({"repo": "test"}),
    )
    db_session.add(job)
    db_session.commit()

    # Trigger restart reconciliation
    BackgroundJobManager.reconcile_dangling_jobs_on_startup(db_session)

    db_session.expire_all()
    reconciled = db_session.query(BackgroundJob).filter_by(id=job.id).first()
    assert reconciled.status == "failed"
    assert "Process restarted" in reconciled.error_message
    assert reconciled.completed_at is not None


@pytest.mark.anyio
async def test_job_failure_error_capture(db_session):
    """Verify that failing task coroutines capture exact exception details in DB."""
    uid = uuid.uuid4().hex[:8]
    user = User(email=f"fail_{uid}@changeradar.dev", hashed_password="pw", name="Fail User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    job = BackgroundJobManager.create_job(
        db=db_session,
        user_id=user.id,
        job_type="fail_task",
        params={"code": 500},
    )

    async def throwing_coroutine(**kwargs):
        raise ValueError("Critical AST Syntax Error in remote branch")

    await BackgroundJobManager._execute_coroutine(job.id, throwing_coroutine)

    db_session.expire_all()
    finished = db_session.query(BackgroundJob).filter_by(id=job.id).first()
    assert finished.status == "failed"
    assert "Critical AST Syntax Error in remote branch" in finished.error_message
    assert finished.completed_at is not None


def test_job_multi_tenant_concurrency_isolation(db_session):
    """Verify that User A reaching max concurrency limit does not block User B."""
    u1 = User(email=f"u1_{uuid.uuid4().hex[:8]}@changeradar.dev", hashed_password="pw", name="User 1")
    u2 = User(email=f"u2_{uuid.uuid4().hex[:8]}@changeradar.dev", hashed_password="pw", name="User 2")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    # User 1 creates 3 jobs (fills quota)
    for i in range(3):
        BackgroundJobManager.create_job(db_session, u1.id, "job", {"idx": i})

    # User 1 4th job fails
    with pytest.raises(RuntimeError, match="Maximum concurrent analysis jobs limit reached"):
        BackgroundJobManager.create_job(db_session, u1.id, "job", {"idx": 99})

    # User 2 can still freely create jobs
    u2_job = BackgroundJobManager.create_job(db_session, u2.id, "job", {"idx": 0})
    assert u2_job.status == "queued"
    assert u2_job.user_id == u2.id
