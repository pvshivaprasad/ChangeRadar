"""SQLAlchemy ORM database models for ChangeRadar:
- User (authentication and accounts)
- Repository (persisted local code repositories)
- Analysis (persisted change impact reports)
"""
from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def hash_password(password: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 password hash with 32-byte salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return f"{salt}:{pw_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt, expected_hash = hashed_password.split(":")
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()
        return secrets.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    api_token = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), unique=True, index=True, nullable=False)
    default_branch = Column(String(100), default="main", nullable=False)
    file_count = Column(Integer, default=0, nullable=False)
    symbol_count = Column(Integer, default=0, nullable=False)
    edge_count = Column(Integer, default=0, nullable=False)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    analyses = relationship("Analysis", back_populates="repository", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "default_branch": self.default_branch,
            "file_count": self.file_count,
            "symbol_count": self.symbol_count,
            "edge_count": self.edge_count,
            "last_scanned_at": self.last_scanned_at.isoformat() if self.last_scanned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "analysis_count": len(self.analyses) if self.analyses else 0,
        }


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    base_commit = Column(String(100), nullable=False)
    head_commit = Column(String(100), nullable=False)
    risk_level = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    changed_files_count = Column(Integer, default=0, nullable=False)
    changed_symbols_count = Column(Integer, default=0, nullable=False)
    impacted_symbols_count = Column(Integer, default=0, nullable=False)
    recommended_tests_count = Column(Integer, default=0, nullable=False)
    summary_text = Column(Text, nullable=False)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    repository = relationship("Repository", back_populates="analyses")

    def to_dict(self) -> Dict[str, Any]:
        report_data = {}
        if self.report_json:
            try:
                report_data = json.loads(self.report_json)
            except Exception:
                pass

        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "changed_files_count": self.changed_files_count,
            "changed_symbols_count": self.changed_symbols_count,
            "impacted_symbols_count": self.impacted_symbols_count,
            "recommended_tests_count": self.recommended_tests_count,
            "summary_text": self.summary_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "report": report_data,
        }
