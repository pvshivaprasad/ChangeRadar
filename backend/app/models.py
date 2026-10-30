"""SQLAlchemy ORM database models for ChangeRadar:
- User (authentication and accounts)
- Repository (persisted code repositories with ownership)
- Analysis (persisted change impact reports with status and ownership)
"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import secrets
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
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


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hex digest of a raw session token for secure database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    token_prefix = Column(String(16), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_accessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(100), nullable=True)

    user = relationship("User", back_populates="sessions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    api_token = Column(String(255), unique=True, index=True, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")

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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False, index=True)
    repo_type = Column(String(50), default="local", nullable=False)  # local, sample, workspace
    default_branch = Column(String(100), default="main", nullable=False)
    file_count = Column(Integer, default=0, nullable=False)
    symbol_count = Column(Integer, default=0, nullable=False)
    edge_count = Column(Integer, default=0, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="repositories")
    analyses = relationship("Analysis", back_populates="repository")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "path": self.path,
            "repo_type": self.repo_type,
            "default_branch": self.default_branch,
            "file_count": self.file_count,
            "symbol_count": self.symbol_count,
            "edge_count": self.edge_count,
            "is_archived": self.is_archived,
            "last_scanned_at": self.last_scanned_at.isoformat() if self.last_scanned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "analysis_count": len([a for a in self.analyses if a.status == "completed"]) if self.analyses else 0,
        }


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    repo_name = Column(String(255), nullable=False, default="")
    repo_path = Column(String(1024), nullable=False, default="")
    base_commit = Column(String(100), nullable=False)
    head_commit = Column(String(100), nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # pending, running, completed, failed
    risk_level = Column(String(50), default="low", nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    changed_files_count = Column(Integer, default=0, nullable=False)
    changed_symbols_count = Column(Integer, default=0, nullable=False)
    impacted_symbols_count = Column(Integer, default=0, nullable=False)
    recommended_tests_count = Column(Integer, default=0, nullable=False)
    summary_text = Column(Text, default="", nullable=False)
    error_message = Column(Text, nullable=True)
    report_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="analyses")
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
            "user_id": self.user_id,
            "repository_id": self.repository_id,
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "status": self.status,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "changed_files_count": self.changed_files_count,
            "changed_symbols_count": self.changed_symbols_count,
            "impacted_symbols_count": self.impacted_symbols_count,
            "recommended_tests_count": self.recommended_tests_count,
            "summary_text": self.summary_text,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "report": report_data,
        }
