"""Safe Repository Storage & Deployment Architecture for ChangeRadar.

Provides:
- User-partitioned isolated workspace storage
- Controlled server-side sample repository for public demos
- Local development scanning restrictions
- Path traversal & symlink recursion defenses
- Repository resource & file-size limits
- Safe cleanup of temporary clones and workspaces
"""
import os
import shutil
from typing import Optional, Tuple
from fastapi import HTTPException, status

from .config import settings


def get_storage_root() -> str:
    """Returns absolute path to the base repository storage directory."""
    root = os.path.abspath(settings.repo_storage_dir)
    os.makedirs(root, exist_ok=True)
    return root


def get_user_storage_dir(user_id: int) -> str:
    """Returns absolute path to an isolated user repository sandbox."""
    user_dir = os.path.join(get_storage_root(), f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_controlled_sample_dir() -> str:
    """Returns path to the pre-packaged server-side sample repository."""
    try:
        from tests.fixtures.setup_fixture import ensure_synthetic_repo
        return ensure_synthetic_repo()
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sample_path = os.path.abspath(os.path.join(current_dir, "..", "tests", "fixtures", "synthetic_repo"))
        return sample_path


def check_resource_limits(repo_path: str) -> None:
    """
    Enforces maximum file count and total byte limits to prevent
    resource exhaustion attacks on the server.
    """
    total_files = 0
    total_bytes = 0

    for root, dirs, files in os.walk(repo_path, followlinks=False):
        # Ignore common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "dist", "build", "venv", ".venv"}]
        for f in files:
            total_files += 1
            if total_files > settings.max_repo_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Repository exceeds file limit ({settings.max_repo_files} files maximum).",
                )
            file_path = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(file_path)
            except OSError:
                continue
            if total_bytes > settings.max_repo_size_bytes:
                max_mb = settings.max_repo_size_bytes // (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Repository exceeds total size limit ({max_mb} MB maximum).",
                )


def validate_repo_access(
    repo_path: str,
    user_id: int,
    is_sample: bool = False,
) -> Tuple[str, str]:
    """
    Validates repository access based on deployment environment and user ownership.
    Returns (resolved_path, repo_type).

    repo_type values:
    - 'sample': Controlled server fixture (read-only demo)
    - 'workspace': User's isolated sandbox storage
    - 'local': Local developer machine path (permitted ONLY in local development)
    """
    sample_dir = get_controlled_sample_dir()

    # Reject empty path unless explicitly marked as sample
    if not repo_path or not repo_path.strip():
        if is_sample:
            return sample_dir, "sample"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository path cannot be empty.",
        )

    clean_input = repo_path.strip()
    # Case 1: Client explicitly requested the controlled sample demo
    if is_sample or clean_input in {"sample", "controlled_sample", "synthetic_repo"}:
        return sample_dir, "sample"

    try:
        resolved = os.path.abspath(os.path.realpath(clean_input))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid repository path format: {exc}",
        )

    if not os.path.isdir(resolved):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository directory does not exist or is inaccessible: {clean_input}",
        )

    # Case 2: Path points directly to the server's controlled sample
    if resolved == sample_dir or resolved.startswith(sample_dir + os.sep):
        return sample_dir, "sample"

    # Case 3: Path resides in user's isolated workspace sandbox
    user_dir = get_user_storage_dir(user_id)
    try:
        if os.path.commonpath([resolved, user_dir]) == user_dir:
            check_resource_limits(resolved)
            return resolved, "workspace"
    except ValueError:
        pass  # Different drives or roots

    # Case 4: Local development path scanning (ALLOWED ONLY IN LOCAL DEV)
    if settings.environment == "development" and settings.allow_local_dev_scanning:
        # Import the existing path validator (system folder & drive root rejection)
        from .main import validate_safe_repo_path
        safe_path = validate_safe_repo_path(resolved)
        check_resource_limits(safe_path)
        return safe_path, "local"

    # Case 5: Remote deployment without authorized sandbox path -> Strictly Rejected
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Direct server filesystem scanning is restricted in remote deployments. "
            "Please use the controlled sample repository or user workspace storage."
        ),
    )


def cleanup_user_repository(user_id: int, repo_identifier: str) -> bool:
    """Safely cleans up a repository directory inside the user's isolated workspace."""
    user_dir = get_user_storage_dir(user_id)
    target = os.path.abspath(os.path.join(user_dir, repo_identifier))
    try:
        if os.path.commonpath([target, user_dir]) == user_dir and os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
            return True
    except Exception:
        pass
    return False
