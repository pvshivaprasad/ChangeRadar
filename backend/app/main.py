from datetime import datetime, timezone, timedelta
import json
import os
import re
import secrets
import time
from typing import Any, Dict, List, Optional
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, check_database_connection, get_db, init_db
from . import models
from .storage import (
    check_resource_limits,
    get_controlled_sample_dir,
    validate_repo_access,
)
from .scanner import (
    ImpactAnalysisReport,
    RepositoryScanner,
    ScanSummary,
    run_impact_analysis,
)
from .github import GitHubClient, GitHubClientError, GitHubService, format_pr_comment
from .historical import HistoricalIntelligenceService
from .jobs import BackgroundJobManager
from .security import verify_github_webhook_signature, mask_token

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables on application launch."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Connected software change impact intelligence platform.",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins_list = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if settings.frontend_origin not in cors_origins_list:
    cors_origins_list.append(settings.frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
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


class ScanRequest(BaseModel):
    repo_path: str


class AnalyzeRequest(BaseModel):
    repo_path: str
    base_commit: str = "HEAD~1"
    head_commit: str = "HEAD"


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


class SlidingWindowRateLimiter:
    """Sliding window rate limiter to mitigate credential brute-force attacks."""
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: Dict[str, List[float]] = {}

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        active = [t for t in self.hits.get(client_key, []) if t > cutoff]
        if len(active) >= self.max_requests:
            self.hits[client_key] = active
            return False
        active.append(now)
        self.hits[client_key] = active
        return True


auth_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_auth_requests,
    window_seconds=60,
)


def verify_csrf_origin(request: Request) -> None:
    """
    Validates Origin/Referer headers on state-changing requests to defend
    against cross-origin request forgery with cookie credentials.
    """
    origin = request.headers.get("origin")
    if not origin:
        return  # Non-browser clients (CLI, test client) do not send Origin header

    allowed = {
        settings.frontend_origin.rstrip("/"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }
    cleaned_origin = origin.rstrip("/")
    if cleaned_origin not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"CSRF protection: request origin '{origin}' is not authorized.",
        )


def set_auth_cookie(response: Response, raw_token: str, request: Request) -> None:
    """Sets a secure, HttpOnly, SameSite session cookie with environment-aware flags."""
    is_secure = (
        settings.session_cookie_secure
        if settings.session_cookie_secure is not None
        else (settings.environment != "development" or request.url.scheme == "https")
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        httponly=True,
        samesite=settings.session_cookie_samesite,
        secure=is_secure,
        max_age=settings.session_expire_days * 24 * 3600,
        path="/",
    )


def extract_raw_token(
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
) -> Optional[str]:
    """Extracts raw authentication token from Bearer header or HttpOnly cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    if session_token:
        return session_token.strip()
    return None


def get_current_user(
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Extracts and validates session token using SHA-256 hashed database lookup.
    Rejects expired sessions, updates last accessed timestamp, and supports
    legacy dev tokens for backward compatibility.
    """
    token = extract_raw_token(authorization, session_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or invalid.",
        )

    now_utc = datetime.now(timezone.utc)
    token_hash = models.hash_token(token)

    # 1. Primary path: Hashed session token in user_sessions table
    session_rec = db.query(models.UserSession).filter_by(token_hash=token_hash).first()
    if session_rec:
        expires_at = session_rec.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        user_expires_at = session_rec.user.token_expires_at
        if user_expires_at and user_expires_at.tzinfo is None:
            user_expires_at = user_expires_at.replace(tzinfo=timezone.utc)
        if now_utc > expires_at or (user_expires_at and now_utc > user_expires_at):
            db.delete(session_rec)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please log in again.",
            )
        session_rec.last_accessed_at = now_utc
        db.commit()
        return session_rec.user

    # 2. Legacy / dev token fallback: check plaintext api_token on users table
    user = db.query(models.User).filter_by(api_token=token).first()
    if user:
        if user.token_expires_at:
            expires_at = user.token_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now_utc > expires_at:
                user.api_token = None
                user.token_expires_at = None
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Your session has expired. Please log in again.",
                )
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid authentication token.",
    )


def get_optional_current_user(
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    """Optional user dependency for public demo endpoints."""
    try:
        return get_current_user(authorization, session_token, db)
    except HTTPException:
        return None


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
        version="1.0.0",
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
def register(
    req: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Registers a new user account with PBKDF2 hashed password and SHA-256 hashed session."""
    verify_csrf_origin(request)
    client_ip = request.client.host if request.client else "unknown"
    if not auth_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please wait a minute before trying again.",
            headers={"Retry-After": "60"},
        )

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

    raw_token = secrets.token_urlsafe(32)
    token_hash = models.hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.session_expire_days)

    user = models.User(
        email=clean_email,
        name=req.name.strip(),
        hashed_password=models.hash_password(req.password),
        api_token=raw_token,
        token_expires_at=expires_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Persist secure hashed session in user_sessions table
    session_record = models.UserSession(
        user_id=user.id,
        token_hash=token_hash,
        token_prefix=raw_token[:8],
        expires_at=expires_at,
        created_at=now,
        last_accessed_at=now,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip,
    )
    db.add(session_record)
    db.commit()

    set_auth_cookie(response, raw_token, request)
    return AuthResponse(token=raw_token, user=UserResponse(**user.to_dict()))


@app.post(f"{settings.api_v1_prefix}/auth/login", response_model=AuthResponse, tags=["auth"])
def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Verifies credentials, generates distinct SHA-256 hashed session, and sets HttpOnly cookie."""
    verify_csrf_origin(request)
    client_ip = request.client.host if request.client else "unknown"
    if not auth_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute before trying again.",
            headers={"Retry-After": "60"},
        )

    clean_email = req.email.strip().lower()
    user = db.query(models.User).filter_by(email=clean_email).first()

    if not user or not models.verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    # Issue distinct session (enables multiple coexisting sessions across devices)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.session_expire_days)
    raw_token = secrets.token_urlsafe(32)
    token_hash = models.hash_token(raw_token)

    session_record = models.UserSession(
        user_id=user.id,
        token_hash=token_hash,
        token_prefix=raw_token[:8],
        expires_at=expires_at,
        created_at=now,
        last_accessed_at=now,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip,
    )
    db.add(session_record)

    # Update legacy token on user model for backward compatibility
    user.api_token = raw_token
    user.token_expires_at = expires_at
    db.commit()

    set_auth_cookie(response, raw_token, request)
    return AuthResponse(token=raw_token, user=UserResponse(**user.to_dict()))


@app.post(f"{settings.api_v1_prefix}/auth/logout", tags=["auth"])
def logout(
    request: Request,
    response: Response,
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Invalidates ONLY the current active session in database and clears authentication cookie."""
    verify_csrf_origin(request)
    token = extract_raw_token(authorization, session_token)
    if token:
        token_hash = models.hash_token(token)
        session_rec = db.query(models.UserSession).filter_by(token_hash=token_hash).first()
        if session_rec:
            db.delete(session_rec)
        if current_user.api_token == token:
            current_user.api_token = None
            current_user.token_expires_at = None
        db.commit()

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )
    return {"message": "Logged out successfully."}


@app.get(f"{settings.api_v1_prefix}/auth/me", response_model=UserResponse, tags=["auth"])
def get_me(user: models.User = Depends(get_current_user)) -> UserResponse:
    """Returns authenticated user profile."""
    return UserResponse(**user.to_dict())


# ---------------------------------------------------------------------------
# Repository Persistence Endpoints (Scoped strictly to current_user)
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/repositories", tags=["repositories"])
def list_repositories(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Returns all active persisted repositories belonging to the authenticated user."""
    repos = (
        db.query(models.Repository)
        .filter_by(user_id=current_user.id, is_archived=False)
        .order_by(models.Repository.id.desc())
        .all()
    )
    return [r.to_dict() for r in repos]


@app.post(f"{settings.api_v1_prefix}/repositories", tags=["repositories"])
def create_or_import_repository(
    req: CreateRepoRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Imports and persists a local repository for the authenticated user.
    Validates path safety, scans AST symbols, and stores repository in database.
    """
    safe_path, repo_type = validate_repo_access(req.path, current_user.id)

    # Scan the repository
    try:
        scanner = RepositoryScanner(safe_path)
        scan_summary = scanner.scan()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to scan repository: {exc}")

    repo_name = req.name.strip() if req.name and req.name.strip() else os.path.basename(safe_path)

    # Check if already registered by this user
    existing = db.query(models.Repository).filter_by(user_id=current_user.id, path=safe_path).first()
    if existing:
        existing.name = repo_name
        existing.repo_type = repo_type
        existing.default_branch = req.default_branch
        existing.file_count = scan_summary.file_count
        existing.symbol_count = scan_summary.symbol_count
        existing.edge_count = scan_summary.edge_count
        existing.is_archived = False
        existing.last_scanned_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing.to_dict()

    repo = models.Repository(
        user_id=current_user.id,
        name=repo_name,
        path=safe_path,
        repo_type=repo_type,
        default_branch=req.default_branch,
        file_count=scan_summary.file_count,
        symbol_count=scan_summary.symbol_count,
        edge_count=scan_summary.edge_count,
        is_archived=False,
        last_scanned_at=datetime.now(timezone.utc),
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo.to_dict()


@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}", tags=["repositories"])
def get_repository(
    repo_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id, is_archived=False).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo.to_dict()


@app.delete(f"{settings.api_v1_prefix}/repositories/{{repo_id}}", tags=["repositories"])
def delete_repository(
    repo_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    # Archival Policy: Mark as archived so historical analysis reports are never lost
    repo.is_archived = True
    db.commit()
    return {"message": f"Repository '{repo.name}' removed from active workspace. Historical analyses are preserved."}


@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/analyses", tags=["repositories"])
def list_repository_analyses(
    repo_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    analyses = (
        db.query(models.Analysis)
        .filter_by(repository_id=repo_id, user_id=current_user.id)
        .order_by(models.Analysis.id.desc())
        .all()
    )
    return [a.to_dict() for a in analyses]


@app.post(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/analyze", tags=["repositories"])
def analyze_persisted_repository(
    repo_id: int,
    req: AnalyzeRepoRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Runs change impact analysis on a persisted repository and saves the report with status tracking."""
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    # Record analysis run with status="running"
    analysis_record = models.Analysis(
        user_id=current_user.id,
        repository_id=repo.id,
        repo_name=repo.name,
        repo_path=repo.path,
        base_commit=req.base_commit,
        head_commit=req.head_commit,
        status="running",
        risk_level="pending",
        risk_score=0.0,
        summary_text="Analysis in progress...",
        report_json="{}",
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    try:
        report = run_impact_analysis(
            repo_path=repo.path,
            base_commit=req.base_commit,
            head_commit=req.head_commit,
        )
        report_dict = report.model_dump()
        analysis_record.status = "completed"
        analysis_record.risk_level = report.risk_level
        analysis_record.risk_score = report.risk_score
        analysis_record.changed_files_count = len(report.changed_files)
        analysis_record.changed_symbols_count = len(report.changed_symbols)
        analysis_record.impacted_symbols_count = len(report.impacted_symbols)
        analysis_record.recommended_tests_count = len(report.recommended_tests)
        analysis_record.summary_text = report.summary_text
        analysis_record.report_json = json.dumps(report_dict)
        db.commit()
        db.refresh(analysis_record)
        return analysis_record.to_dict()
    except ValueError as exc:
        analysis_record.status = "failed"
        analysis_record.error_message = str(exc)
        analysis_record.summary_text = f"Analysis failed: {exc}"
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        analysis_record.status = "failed"
        analysis_record.error_message = str(exc)
        analysis_record.summary_text = f"Analysis failed: {exc}"
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        analysis_record.status = "failed"
        analysis_record.error_message = str(exc)
        analysis_record.summary_text = f"Analysis error: {exc}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}")


# ---------------------------------------------------------------------------
# Direct Analysis Endpoints (Scoped strictly to current_user)
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/analyses", tags=["analyses"])
def list_all_analyses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Returns all historical analyses belonging to the authenticated user."""
    analyses = (
        db.query(models.Analysis)
        .filter_by(user_id=current_user.id)
        .order_by(models.Analysis.id.desc())
        .all()
    )
    return [a.to_dict() for a in analyses]


@app.get(f"{settings.api_v1_prefix}/analyses/{{analysis_id}}", tags=["analyses"])
def get_analysis_by_id(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves a specific analysis by ID, strictly enforcing user ownership."""
    analysis = db.query(models.Analysis).filter_by(id=analysis_id, user_id=current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")
    return analysis.to_dict()


# ---------------------------------------------------------------------------
# Direct Intelligence & Sample Endpoints
# ---------------------------------------------------------------------------

@app.post(f"{settings.api_v1_prefix}/scan", response_model=ScanSummary, tags=["intelligence"])
def scan_repository(
    req: ScanRequest,
    current_user: Optional[models.User] = Depends(get_optional_current_user),
) -> ScanSummary:
    """Scans repository for AST symbols and dependency edges with safe deployment validation."""
    user_id = current_user.id if current_user else 0
    safe_path, _ = validate_repo_access(req.repo_path, user_id)
    try:
        scanner = RepositoryScanner(safe_path)
        return scanner.scan()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/analyze", response_model=ImpactAnalysisReport, tags=["intelligence"])
def analyze_change(
    req: AnalyzeRequest,
    current_user: Optional[models.User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ImpactAnalysisReport:
    """Executes full change impact analysis between two commit revisions with safe deployment validation."""
    user_id = current_user.id if current_user else 0
    safe_path, _ = validate_repo_access(req.repo_path, user_id)
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

    # Automatically persist analysis for authenticated user (or dev user)
    user = current_user or db.query(models.User).filter_by(email="dev@changeradar.io").first()
    if user:
        try:
            repo = db.query(models.Repository).filter_by(user_id=user.id, path=safe_path).first()
            repo_id = repo.id if repo else None
            repo_name = repo.name if repo else os.path.basename(safe_path)

            analysis_record = models.Analysis(
                user_id=user.id,
                repository_id=repo_id,
                repo_name=repo_name,
                repo_path=safe_path,
                base_commit=req.base_commit,
                head_commit=req.head_commit,
                status="completed",
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
def run_sample_analysis(
    current_user: Optional[models.User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ImpactAnalysisReport:
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

    # Ensure synthetic repository and analysis are registered for this user
    user = current_user or db.query(models.User).filter_by(email="dev@changeradar.io").first()
    if user:
        try:
            repo = db.query(models.Repository).filter_by(user_id=user.id, path=synth_path).first()
            if not repo:
                scanner = RepositoryScanner(synth_path)
                scan_summary = scanner.scan()
                repo = models.Repository(
                    user_id=user.id,
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
                user_id=user.id,
                repository_id=repo.id,
                repo_name=repo.name,
                repo_path=repo.path,
                base_commit="HEAD~1",
                head_commit="HEAD",
                status="completed",
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


# ---------------------------------------------------------------------------
# Readiness Check
# ---------------------------------------------------------------------------

@app.get("/ready", tags=["health"])
@app.get(f"{settings.api_v1_prefix}/ready", tags=["health"])
def check_readiness():
    """Verifies that the database and application are ready to serve requests."""
    db_status = check_database_connection()
    if not db_status["connected"]:
        raise HTTPException(status_code=503, detail=f"Database not ready: {db_status.get('error')}")
    return {"status": "ready", "database": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# GitHub Integration Endpoints
# ---------------------------------------------------------------------------

class GitHubConnectRequest(BaseModel):
    access_token: str
    account_type: str = "oauth"
    scopes: str = "repo,read:user"


class GitHubImportRequest(BaseModel):
    full_name: str


class PullRequestAnalyzeRequest(BaseModel):
    post_comment: bool = False
    background: bool = False


class PullRequestCommentRequest(BaseModel):
    body_markdown: Optional[str] = None


@app.post(f"{settings.api_v1_prefix}/github/connect", tags=["github"])
async def connect_github_account(
    req: GitHubConnectRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Securely links a GitHub account or personal access token to the current user."""
    svc = GitHubService(db)
    try:
        res = await svc.connect_account(
            user_id=current_user.id,
            access_token=req.access_token,
            account_type=req.account_type,
            scopes=req.scopes,
        )
        return res
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"GitHub connection failed: {str(exc)}")


@app.delete(f"{settings.api_v1_prefix}/github/disconnect", tags=["github"])
def disconnect_github_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnects and revokes GitHub credentials for the current user."""
    svc = GitHubService(db)
    ok = svc.disconnect_account(current_user.id)
    return {"status": "disconnected" if ok else "not_connected"}


@app.get(f"{settings.api_v1_prefix}/github/status", tags=["github"])
def get_github_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the current user's GitHub connection status and masked credentials."""
    svc = GitHubService(db)
    account = svc.get_account(current_user.id)
    if not account:
        return {"connected": False}
    return {
        "connected": True,
        "github_username": account.github_username,
        "account_type": account.account_type,
        "scopes": account.scopes,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }


@app.get(f"{settings.api_v1_prefix}/github/repositories", tags=["github"])
async def list_github_repositories(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists authorized repositories available to the user on GitHub."""
    svc = GitHubService(db)
    try:
        repos = await svc.list_user_repositories(current_user.id)
        return repos
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/github/repositories/import", tags=["github"])
async def import_github_repository(
    req: GitHubImportRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Imports a GitHub repository into an isolated user workspace."""
    svc = GitHubService(db)
    try:
        repo = await svc.import_repository(user_id=current_user.id, full_name=req.full_name)
        return repo.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to import repository: {str(exc)}")


@app.get(f"{settings.api_v1_prefix}/github/repositories/{{repo_id}}/pulls", tags=["github"])
async def list_github_pull_requests(
    repo_id: int,
    state: str = "open",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches open pull requests for an imported repository."""
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")
    if not repo.github_repo_full_name:
        raise HTTPException(status_code=400, detail="Repository is not linked to GitHub")

    owner, repo_name = repo.github_repo_full_name.split("/")
    svc = GitHubService(db)
    client = svc.get_client(current_user.id)
    try:
        pulls = await client.list_pull_requests(owner, repo_name, state=state)
        return pulls
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pull requests: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/github/repositories/{{repo_id}}/pulls/{{pr_number}}/analyze", tags=["github"])
async def analyze_github_pull_request(
    repo_id: int,
    pr_number: int,
    req: PullRequestAnalyzeRequest = PullRequestAnalyzeRequest(),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Runs change blast radius analysis on an open pull request."""
    svc = GitHubService(db)
    if req.background:
        job = BackgroundJobManager.create_job(
            db=db,
            user_id=current_user.id,
            job_type="pr_analysis",
            params={"repo_id": repo_id, "pr_number": pr_number, "post_comment": req.post_comment},
        )
        async def _run_task():
            async_svc = GitHubService(db)
            an = await async_svc.analyze_pull_request(
                user_id=current_user.id,
                repo_id=repo_id,
                pr_number=pr_number,
                post_comment=req.post_comment,
            )
            return an.to_dict()

        BackgroundJobManager.run_async(job.id, _run_task)
        return {"job_id": job.id, "status": "queued"}

    try:
        analysis = await svc.analyze_pull_request(
            user_id=current_user.id,
            repo_id=repo_id,
            pr_number=pr_number,
            post_comment=req.post_comment,
        )
        return analysis.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pull request analysis failed: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/github/repositories/{{repo_id}}/pulls/{{pr_number}}/comment", tags=["github"])
async def post_github_pr_comment(
    repo_id: int,
    pr_number: int,
    req: PullRequestCommentRequest = PullRequestCommentRequest(),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Posts or updates an analysis summary comment on a pull request."""
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo or not repo.github_repo_full_name:
        raise HTTPException(status_code=404, detail="Repository not found or not connected to GitHub")

    owner, repo_name = repo.github_repo_full_name.split("/")
    svc = GitHubService(db)
    client = svc.get_client(current_user.id)

    # If body_markdown not explicitly provided, build from latest analysis of this PR
    body_md = req.body_markdown
    if not body_md:
        latest_analysis = (
            db.query(models.Analysis)
            .filter_by(repository_id=repo_id, pr_number=pr_number, status="completed")
            .order_by(models.Analysis.created_at.desc())
            .first()
        )
        if not latest_analysis or not latest_analysis.report_json:
            raise HTTPException(status_code=400, detail="No completed analysis exists for this PR. Run analysis first.")
        rep_dict = json.loads(latest_analysis.report_json)
        rep = ImpactAnalysisReport(**rep_dict)
        body_md = format_pr_comment(rep, pr_number, latest_analysis.pr_title or f"PR #{pr_number}")

    try:
        res = await client.create_or_update_pr_comment(
            owner=owner,
            repo=repo_name,
            pull_number=pr_number,
            body_markdown=body_md,
        )
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to post comment: {str(exc)}")


@app.post(f"{settings.api_v1_prefix}/github/webhook", tags=["github"])
async def receive_github_webhook(
    request: Request,
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
):
    """Receives and processes incoming GitHub webhooks with HMAC-SHA256 signature verification."""
    body_bytes = await request.body()
    svc = GitHubService(db)
    try:
        res = await svc.handle_webhook(
            delivery_id=x_github_delivery,
            event_type=x_github_event,
            payload_bytes=body_bytes,
            signature_header=x_hub_signature_256,
        )
        return res
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}")


# ---------------------------------------------------------------------------
# Historical Change Intelligence Endpoints
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/historical/patterns", tags=["historical"])
def get_historical_patterns(
    repo_id: int,
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns recurring change patterns, hotspots, and historical risk trends for a repository."""
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")

    hist_svc = HistoricalIntelligenceService(db)
    return hist_svc.compute_change_patterns(repository_id=repo_id, user_id=current_user.id, limit=limit)


@app.get(f"{settings.api_v1_prefix}/repositories/{{repo_id}}/historical/compare", tags=["historical"])
def compare_historical_analyses(
    repo_id: int,
    analysis_a_id: int,
    analysis_b_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compares two historical analyses to discover blast radius progression and test drift."""
    repo = db.query(models.Repository).filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied")

    hist_svc = HistoricalIntelligenceService(db)
    try:
        return hist_svc.compare_analyses(
            analysis_id_a=analysis_a_id,
            analysis_id_b=analysis_b_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Background Jobs Endpoints
# ---------------------------------------------------------------------------

@app.get(f"{settings.api_v1_prefix}/jobs/{{job_id}}", tags=["jobs"])
def get_background_job_status(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Checks the status and results of an asynchronous background job."""
    job = (
        db.query(models.BackgroundJob)
        .filter_by(id=job_id, user_id=current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    return job.to_dict()

