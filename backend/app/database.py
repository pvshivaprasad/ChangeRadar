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

        # Seed default development user if not present
        db = SessionLocal()
        try:
            user = db.query(models.User).filter_by(email="dev@changeradar.io").first()
            if not user:
                dev_user = models.User(
                    email="dev@changeradar.io",
                    name="Lead Engineer",
                    hashed_password=models.hash_password("changeradar2026"),
                    api_token="dev-token-lead-engineer",
                )
                db.add(dev_user)
                db.commit()
        finally:
            db.close()
        return True
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc)
        return False

