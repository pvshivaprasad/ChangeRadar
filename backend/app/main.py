from datetime import datetime, timezone
import os
import re
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .database import check_database_connection
from .scanner import (
    ImpactAnalysisReport,
    RepositoryScanner,
    ScanSummary,
    run_impact_analysis,
)

app = FastAPI(
    title=settings.app_name,
    description="Software change impact intelligence API.",
    version="0.1.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


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


def get_synthetic_repo_path() -> str:
    try:
        from tests.fixtures.setup_fixture import ensure_synthetic_repo
        return ensure_synthetic_repo()
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, "..", "tests", "fixtures", "synthetic_repo"))


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
def analyze_change(req: AnalyzeRequest) -> ImpactAnalysisReport:
    """Executes full change impact analysis between two commit revisions."""
    safe_path = validate_safe_repo_path(req.repo_path)
    try:
        return run_impact_analysis(
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


@app.get(f"{settings.api_v1_prefix}/sample/run", response_model=ImpactAnalysisReport, tags=["sample"])
def run_sample_analysis() -> ImpactAnalysisReport:
    """Executes live change impact analysis on the verified synthetic Python repository fixture."""
    synth_path = get_synthetic_repo_path()
    if not os.path.isdir(synth_path):
        raise HTTPException(status_code=404, detail="Synthetic repository fixture not found on server")
    try:
        return run_impact_analysis(
            repo_path=synth_path,
            base_commit="HEAD~1",
            head_commit="HEAD",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sample analysis failure: {str(exc)}")


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
