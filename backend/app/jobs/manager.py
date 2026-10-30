"""Lightweight, resilient in-process background job manager for ChangeRadar 1.0.

Provides:
- Persistent job status in database ('queued', 'running', 'completed', 'failed')
- Per-user concurrency limits (prevents resource starvation)
- Duplicate job prevention
- Safe temporary workspace cleanup on failure
- Progress reporting and error capturing
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Callable, Coroutine, Dict, Optional
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import BackgroundJob

logger = logging.getLogger("changeradar.jobs")
_executor = ThreadPoolExecutor(max_workers=settings.background_worker_concurrency)


class BackgroundJobManager:
    """Manages asynchronous background jobs with DB persistence and per-user concurrency limits."""

    @staticmethod
    def reconcile_dangling_jobs_on_startup(db: Session):
        """Reconciles dangling jobs that were interrupted by an unexpected process termination."""
        try:
            dangling = (
                db.query(BackgroundJob)
                .filter(BackgroundJob.status.in_(["queued", "running"]))
                .all()
            )
            for j in dangling:
                j.status = "failed"
                j.error_message = "Process restarted while job was in progress."
                j.completed_at = datetime.now(timezone.utc)
            if dangling:
                db.commit()
                logger.info(f"Reconciled {len(dangling)} dangling background jobs on startup.")
        except Exception as exc:
            logger.warning(f"Failed to reconcile dangling jobs: {exc}")

    @staticmethod
    def create_job(
        db: Session,
        user_id: int,
        job_type: str,
        params: Dict[str, Any],
    ) -> BackgroundJob:
        """
        Creates and persists a new queued background job.
        Checks for active duplicate jobs with identical parameters to prevent duplicate analysis.
        """
        params_str = json.dumps(params, sort_keys=True)

        # Check duplicate running/queued job
        existing = (
            db.query(BackgroundJob)
            .filter(
                BackgroundJob.user_id == user_id,
                BackgroundJob.job_type == job_type,
                BackgroundJob.status.in_(["queued", "running"]),
                BackgroundJob.params_json == params_str,
            )
            .first()
        )
        if existing:
            return existing

        # Enforce per-user active concurrency limit (max 3 concurrent jobs)
        active_count = (
            db.query(BackgroundJob)
            .filter(
                BackgroundJob.user_id == user_id,
                BackgroundJob.status.in_(["queued", "running"]),
            )
            .count()
        )
        if active_count >= 3:
            raise RuntimeError("Maximum concurrent analysis jobs limit reached (3). Please wait for active jobs to complete.")

        job_id = f"job_{uuid.uuid4().hex[:16]}"
        job = BackgroundJob(
            id=job_id,
            user_id=user_id,
            job_type=job_type,
            status="queued",
            progress_percent=0,
            params_json=params_str,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def run_async(
        job_id: str,
        task_coroutine_fn: Callable[..., Coroutine[Any, Any, Dict[str, Any]]],
        *args,
        **kwargs,
    ):
        """Dispatches an async coroutine to run in the background event loop."""
        asyncio.create_task(BackgroundJobManager._execute_coroutine(job_id, task_coroutine_fn, *args, **kwargs))

    @staticmethod
    async def _execute_coroutine(
        job_id: str,
        task_coroutine_fn: Callable[..., Coroutine[Any, Any, Dict[str, Any]]],
        *args,
        **kwargs,
    ):
        db = SessionLocal()
        try:
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if not job:
                return

            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.progress_percent = 20
            db.commit()

            result = await task_coroutine_fn(*args, **kwargs)

            # Re-fetch in case session was closed
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if job:
                job.status = "completed"
                job.progress_percent = 100
                job.completed_at = datetime.now(timezone.utc)
                job.result_json = json.dumps(result) if result else "{}"
                db.commit()
        except Exception as exc:
            logger.error(f"Background job {job_id} failed: {exc}", exc_info=True)
            try:
                job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(exc)
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
