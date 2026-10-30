from datetime import datetime, timezone
import json
import os
import re
import secrets
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, check_database_connection, get_db, init_db
from . import models
from .scanner import (
    ImpactAnalysisReport,
    RepositoryScanner,
    ScanSummary,
    run_impact_analysis,
)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables on application launch."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Software change impact intelligence API.",
    version="0.1.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class DatabaseHealth(BaseModel):
    connected: bool
    dialect: str
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database: DatabaseHealth


class StatusResponse(BaseModel):
    message: str
    environment: str
    version: str
    timestamp: str
    database: DatabaseHealth


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class ScanRequest(BaseModel):
    repo_path: str


class AnalyzeRequest(BaseModel):
    repo_path: str
    base_commit: str = "HEAD~1"
    head_commit: str = "HEAD"


class CreateRepoRequest(BaseModel):
    path: str
    name: Optional[str] = None
    default_branch: str = "main"


class AnalyzeRepoRequest(BaseModel):
    base_commit: str = "HEAD~1"
    head_commit: str = "HEAD"


# ---------------------------------------------------------------------------
# Path & Auth Helpers
# ---------------------------------------------------------------------------

def validate_safe_repo_path(repo_path: str) -> str:
    """
    Validates that repo_path is a legitimate, accessible directory
    and prevents directory traversal or unauthorized access to system root paths.
    """
    if not repo_path or not repo_path.strip():
        raise HTTPException(status_code=400, detail="Repository path cannot be empty.")

    try:
        resolved = os.path.abspath(os.path.realpath(repo_path.strip()))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid path format: {exc}")

    if not os.path.isdir(resolved):
        raise HTTPException(status_code=400, detail=f"Directory does not exist or is not accessible: {repo_path}")

    norm = resolved.replace("\\", "/").rstrip("/").lower()

    # Block drive root directories directly (e.g. "c:", "d:")
    if re.match(r"^[a-z]:$", norm) or norm == "":
        raise HTTPException(status_code=403, detail="Scanning drive root directly is forbidden for security.")

    # Block protected system folders
    forbidden_prefixes = [
        "c:/windows",
        "c:/winnt",
        "c:/program files",
        "c:/program files (x86)",
        "c:/system volume information",
        "c:/recovery",
        "/etc",
        "/sys",
        "/proc",
        "/dev",
        "/boot",
        "/root",
        "/usr",
        "/bin",
        "/sbin",
        "/var",
    ]
    for forbidden in forbidden_prefixes:
        if norm == forbidden or norm.startswith(forbidden + "/"):
            raise HTTPException(status_code=403, detail=f"Access to protected system path '{norm}' is forbidden.")

    return resolved


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    """Dependency that extracts and validates the Bearer token against database users."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or invalid.",
        )
    token = authorization.split(" ", 1)[1].strip()
    user = db.query(models.User).filter_by(api_token=token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid authentication token.",
        )
    return user


def get_synthetic_repo_path() -> str:
    try:
        from tests.fixtures.setup_fixture import ensure_synthetic_repo
        return ensure_synthetic_repo()
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, "..", "tests", "fixtures", "synthetic_repo"))


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    db_status = check_database_connection()
    overall_status = "healthy" if db_status["connected"] else "degraded"
    return HealthResponse(
        status=overall_status,
        service="changeradar-api",
        version="0.1.1",
        environment=settings.environment,
        database=DatabaseHealth(
            connected=db_status["connected"],
            dialect=db_status["dialect"],
            error=db_status["error"],
        ),
    )


@app.get(f"{settings.api_v1_prefix}/status", response_model=StatusResponse, tags=["system"])
def api_status() -> StatusResponse:
    db_status = check_database_connection()
    return StatusResponse(
        message="ChangeRadar API is ready",
        environment=settings.environment,
        version="0.1.1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=DatabaseHealth(
            connected=db_status["connected"],
            dialect=db_status["dialect"],
            error=db_status["error"],
        ),
    )


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------

@app.post(f"{settings.api_v1_prefix}/auth/register", response_model=AuthResponse, tags=["auth"])
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Registers a new user account with PBKDF2 hashed password."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    if not req.email.strip() or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    clean_email = req.email.strip().lower()
    existing = db.query(models.User).filter_by(email=clean_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    token = secrets.token_urlsafe(32)
    user = models.User(
        email=clean_email,
        name=req.name.strip(),
        hashed_password=models.hash_password(req.password),
        api_token=token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(token=token, user=UserResponse(**user.to_dict()))


@app.post(f"{settings.api_v1_prefix}/auth/login", response_model=AuthResponse, tags=["auth"])
def login(req: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Verifies credentials and returns session token."""
    clean_email = req.email.strip().lower()
    user = db.query(models.User).filter_by(email=clean_email).first()

    if not user or not models.verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    # Issue or refresh token
    if not user.api_token:
        user.api_token = secrets.token_urlsafe(32)
        db.commit()

    return AuthResponse(token=user.api_token, user=UserResponse(**user.to_dict()))


@app.get(f"{settings.api_v1_prefix}/auth/me", response_model=UserResponse, tags=["auth"])
def get_me(user: models.User = Depends(get_current_user)) -> UserResponse:
    """Returns authenticated user profile."""
    return UserResponse(**user.to_dict())


# ---------------------------------------------------------------------------
# Repository Persistence Endpoints
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/repositories", tags=["repositories"])
def list_repositories(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns all persisted repositories in the database."""
    repos = db.query(models.Repository).order_by(models.Repository.id.desc()).all()
    return [r.to_dict() for r in repos]


@app.post(f"{settings.api_v1_prefix}/repositories", tags=["repositories"])
def create_or_import_repository(
    req: CreateRepoRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Imports and persists a local repository.
    Validates path safety, scans AST symbols, and stores repository in database.
    """
    safe_path = validate_safe_repo_path(req.path)

    # Scan the repository
    try:
        scanner = RepositoryScanner(safe_path)
        scan_summary = scanner.scan()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to scan repository: {exc}")

    repo_name = req.name.strip() if req.name and req.name.strip() else os.path.basename(safe_path)

    # Check if already registered
    existing = db.query(models.Repository).filter_by(path=safe_path).first()
    if existing:
        existing.file_count = scan_summary.file_count
        existing.symbol_count = scan_summary.symbol_count
        existing.edge_count = scan_summary.edge_count
        existing.last_scanned_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing.to_dict()

    repo = models.Repository(
        name=repo_name,
        path=safe_path,
        default_branch=req.default_branch,
        file_count=scan_summary.file_count,
        symbol_count=scan_summary.symbol_count,
        edge_count=scan_summary.edge_count,
        last_scanned_at=datetime.now(timezone.utc),
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo.to_dict()


@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}", tags=["repositories"])
def get_repository(repo_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = db.query(models.Repository).filter_by(id=repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo.to_dict()


@app.delete(f"{settings.api_v1_prefix}/repositories/{{repo_id}}", tags=["repositories"])
def delete_repository(repo_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = db.query(models.Repository).filter_by(id=repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    db.delete(repo)
    db.commit()
    return {"message": f"Repository '{repo.name}' deleted successfully."}


@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/analyses", tags=["repositories"])
def list_repository_analyses(repo_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    repo = db.query(models.Repository).filter_by(id=repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    analyses = (
        db.query(models.Analysis)
        .filter_by(repository_id=repo_id)
        .order_by(models.Analysis.id.desc())
        .all()
    )
    return [a.to_dict() for a in analyses]


@app.get(f"{settings.api_v1_prefix}/analyses", tags=["analyses"])
def list_all_analyses(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    analyses = db.query(models.Analysis).order_by(models.Analysis.id.desc()).all()
    return [a.to_dict() for a in analyses]


@app.post(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/analyze", tags=["repositories"])
def analyze_persisted_repository(
    repo_id: int,
    req: AnalyzeRepoRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Runs change impact analysis on a persisted repository and saves the report."""
    repo = db.query(models.Repository).filter_by(id=repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    try:
        report = run_impact_analysis(
            repo_path=repo.path,
            base_commit=req.base_commit,
            head_commit=req.head_commit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}")

    # Persist analysis
    report_dict = report.model_dump()
    analysis_record = models.Analysis(
        repository_id=repo.id,
        base_commit=req.base_commit,
        head_commit=req.head_commit,
        risk_level=report.risk_level,
        risk_score=report.risk_score,
        changed_files_count=len(report.changed_files),
        changed_symbols_count=len(report.changed_symbols),
        impacted_symbols_count=len(report.impacted_symbols),
        recommended_tests_count=len(report.recommended_tests),
        summary_text=report.summary_text,
        report_json=json.dumps(report_dict),
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    return analysis_record.to_dict()


# ---------------------------------------------------------------------------
# Direct Intelligence & Sample Endpoints
# ---------------------------------------------------------------------------

@app.post(f"{settings.api_v1_prefix}/scan", response_model=ScanSummary, tags=["intelligence"])
def scan_repository(req: ScanRequest) -> ScanSummary:
    """Scans local Python repository for AST symbols and dependency edges."""
    safe_path = validate_safe_repo_path(req.repo_path)
    try:
        scanner = RepositoryScanner(safe_path)
        return scanner.scan()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/analyze", response_model=ImpactAnalysisReport, tags=["intelligence"])
def analyze_change(req: AnalyzeRequest, db: Session = Depends(get_db)) -> ImpactAnalysisReport:
    """Executes full change impact analysis between two commit revisions."""
    safe_path = validate_safe_repo_path(req.repo_path)
    try:
        report = run_impact_analysis(
            repo_path=safe_path,
            base_commit=req.base_commit,
            head_commit=req.head_commit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}")

    # Auto-record in DB if repo exists
    repo = db.query(models.Repository).filter_by(path=safe_path).first()
    if repo:
        try:
            analysis_record = models.Analysis(
                repository_id=repo.id,
                base_commit=req.base_commit,
                head_commit=req.head_commit,
                risk_level=report.risk_level,
                risk_score=report.risk_score,
                changed_files_count=len(report.changed_files),
                changed_symbols_count=len(report.changed_symbols),
                impacted_symbols_count=len(report.impacted_symbols),
                recommended_tests_count=len(report.recommended_tests),
                summary_text=report.summary_text,
                report_json=json.dumps(report.model_dump()),
            )
            db.add(analysis_record)
            db.commit()
        except Exception:
            pass

    return report


@app.get(f"{settings.api_v1_prefix}/sample/run", response_model=ImpactAnalysisReport, tags=["sample"])
def run_sample_analysis(db: Session = Depends(get_db)) -> ImpactAnalysisReport:
    """Executes live change impact analysis on the verified synthetic Python repository fixture."""
    synth_path = get_synthetic_repo_path()
    if not os.path.isdir(synth_path):
        raise HTTPException(status_code=404, detail="Synthetic repository fixture not found on server")
    try:
        report = run_impact_analysis(
            repo_path=synth_path,
            base_commit="HEAD~1",
            head_commit="HEAD",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sample analysis failure: {str(exc)}")

    # Ensure synthetic repository is registered and analysis recorded
    try:
        repo = db.query(models.Repository).filter_by(path=synth_path).first()
        if not repo:
            scanner = RepositoryScanner(synth_path)
            scan_summary = scanner.scan()
            repo = models.Repository(
                name="synthetic-payment-auth",
                path=synth_path,
                default_branch="master",
                file_count=scan_summary.file_count,
                symbol_count=scan_summary.symbol_count,
                edge_count=scan_summary.edge_count,
                last_scanned_at=datetime.now(timezone.utc),
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

        analysis_record = models.Analysis(
            repository_id=repo.id,
            base_commit="HEAD~1",
            head_commit="HEAD",
            risk_level=report.risk_level,
            risk_score=report.risk_score,
            changed_files_count=len(report.changed_files),
            changed_symbols_count=len(report.changed_symbols),
            impacted_symbols_count=len(report.impacted_symbols),
            recommended_tests_count=len(report.recommended_tests),
            summary_text=report.summary_text,
            report_json=json.dumps(report.model_dump()),
        )
        db.add(analysis_record)
        db.commit()
    except Exception:
        pass

    return report


@app.get(f"{settings.api_v1_prefix}/sample/scan", response_model=ScanSummary, tags=["sample"])
def scan_sample_repository() -> ScanSummary:
    """Returns scanned AST symbols and call graph for the synthetic Python repository fixture."""
    synth_path = get_synthetic_repo_path()
    if not os.path.isdir(synth_path):
        raise HTTPException(status_code=404, detail="Synthetic repository fixture not found on server")
    try:
        scanner = RepositoryScanner(synth_path)
        return scanner.scan()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sample scan failure: {str(exc)}")
