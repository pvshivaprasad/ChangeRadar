import logging
from typing import Any, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

logger = logging.getLogger("changeradar.database")


def mask_database_url(url_str: str) -> str:
    """Mask passwords and credentials in connection strings for safe logging."""
    try:
        url = make_url(url_str)
        return url.render_as_string(hide_password=True)
    except Exception:
        return "<invalid-db-url>"


def init_engine(db_url: str):
    connect_args: dict[str, Any] = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine = init_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> dict[str, Any]:
    """
    Actively verifies connectivity to the configured database.
    Does not fall back or mask failures; diagnostics avoid leaking credentials.
    """
    masked_url = mask_database_url(settings.database_url)
    dialect = engine.dialect.name
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "connected": True,
            "dialect": dialect,
            "url": masked_url,
            "error": None,
        }
    except Exception as exc:
        logger.error("Database connection failure to %s: %s", masked_url, exc.__class__.__name__)
        return {
            "connected": False,
            "dialect": dialect,
            "url": masked_url,
            "error": f"Connection check failed ({exc.__class__.__name__})",
        }


def init_db() -> bool:
    """Creates database tables and seeds initial local development account if needed."""
    try:
        from . import models  # noqa: F401
        Base.metadata.create_all(bind=engine)

        # Ensure any newly added columns exist in existing SQLite databases
        try:
            with engine.connect() as conn:
                # 1. Repositories table columns
                res = conn.execute(text("PRAGMA table_info(repositories)")).fetchall()
                cols = [r[1] for r in res]
                if cols:
                    if "repo_type" not in cols:
                        conn.execute(text("ALTER TABLE repositories ADD COLUMN repo_type VARCHAR(50) DEFAULT 'local'"))
                    if "github_repo_full_name" not in cols:
                        conn.execute(text("ALTER TABLE repositories ADD COLUMN github_repo_full_name VARCHAR(255)"))
                    if "github_clone_url" not in cols:
                        conn.execute(text("ALTER TABLE repositories ADD COLUMN github_clone_url VARCHAR(1024)"))
                    if "is_private" not in cols:
                        conn.execute(text("ALTER TABLE repositories ADD COLUMN is_private BOOLEAN DEFAULT false"))

                # 2. Analyses table columns
                res_a = conn.execute(text("PRAGMA table_info(analyses)")).fetchall()
                cols_a = [r[1] for r in res_a]
                if cols_a:
                    if "pr_number" not in cols_a:
                        conn.execute(text("ALTER TABLE analyses ADD COLUMN pr_number INTEGER"))
                    if "pr_title" not in cols_a:
                        conn.execute(text("ALTER TABLE analyses ADD COLUMN pr_title VARCHAR(512)"))
                    if "is_github_pr" not in cols_a:
                        conn.execute(text("ALTER TABLE analyses ADD COLUMN is_github_pr BOOLEAN DEFAULT false"))
                    if "github_comment_id" not in cols_a:
                        conn.execute(text("ALTER TABLE analyses ADD COLUMN github_comment_id VARCHAR(100)"))
                    if "analysis_engine_version" not in cols_a:
                        conn.execute(text("ALTER TABLE analyses ADD COLUMN analysis_engine_version VARCHAR(50) DEFAULT '1.0.0'"))
                conn.commit()
        except Exception:
            pass

        # Seed default development user if not present
        db = SessionLocal()
        try:
            from datetime import datetime, timezone, timedelta
            user = db.query(models.User).filter_by(email="dev@changeradar.io").first()
            if not user:
                dev_token = "dev-token-lead-engineer"
                token_hash = models.hash_token(dev_token)
                dev_user = models.User(
                    email="dev@changeradar.io",
                    name="Lead Engineer",
                    hashed_password=models.hash_password("changeradar2026"),
                    api_token=dev_token,
                    token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                )
                db.add(dev_user)
                db.commit()
                db.refresh(dev_user)

                dev_session = models.UserSession(
                    user_id=dev_user.id,
                    token_hash=token_hash,
                    token_prefix=dev_token[:8],
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                    created_at=datetime.now(timezone.utc),
                    last_accessed_at=datetime.now(timezone.utc),
                    user_agent="ChangeRadar System Seed",
                    ip_address="127.0.0.1",
                )
                db.add(dev_session)
                db.commit()
            else:
                if not user.token_expires_at:
                    user.token_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
                    db.commit()
                dev_token = user.api_token or "dev-token-lead-engineer"
                token_hash = models.hash_token(dev_token)
                session = db.query(models.UserSession).filter_by(token_hash=token_hash).first()
                if not session:
                    dev_session = models.UserSession(
                        user_id=user.id,
                        token_hash=token_hash,
                        token_prefix=dev_token[:8],
                        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                        created_at=datetime.now(timezone.utc),
                        last_accessed_at=datetime.now(timezone.utc),
                        user_agent="ChangeRadar System Seed",
                        ip_address="127.0.0.1",
                    )
                    db.add(dev_session)
                    db.commit()

            try:
                from .jobs.manager import BackgroundJobManager
                BackgroundJobManager.reconcile_dangling_jobs_on_startup(db)
            except Exception:
                pass
        finally:
            db.close()
        return True
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc)
        return False

