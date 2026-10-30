import fnmatch
import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Set

from .models import DependencyEdge, ScanSummary, Symbol
from .parser import PythonASTParser

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB limit to prevent memory exhaustion on oversized files

IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    "site-packages",
}


def load_gitignore_patterns(repo_dir: str) -> List[str]:
    """Reads .gitignore rules from repository root if present."""
    gitignore_path = os.path.join(repo_dir, ".gitignore")
    patterns: List[str] = []
    if os.path.isfile(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Normalize pattern
                        patterns.append(line.replace("\\", "/"))
        except Exception:
            pass
    return patterns


def is_path_ignored(rel_path: str, patterns: List[str]) -> bool:
    """Checks whether a relative path matches any .gitignore pattern."""
    clean_path = rel_path.replace("\\", "/").strip("/")
    basename = os.path.basename(clean_path)

    for pat in patterns:
        pat_clean = pat.rstrip("/")
        # Check direct wildcard or basename match
        if fnmatch.fnmatch(basename, pat_clean) or fnmatch.fnmatch(clean_path, pat_clean):
            return True
        # Check if pattern matches a parent directory or prefix
        if pat.endswith("/") and (clean_path == pat_clean or clean_path.startswith(pat_clean + "/")):
            return True
        if clean_path.startswith(pat_clean + "/"):
            return True
    return False


def get_current_commit_sha(repo_dir: str) -> Optional[str]:
    """Retrieves current Git commit SHA if directory is inside a Git repository."""
    try:
        res = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


class RepositoryScanner:
    """
    Safely traverses a local directory, identifies Python source files,
    and runs AST extraction without executing project code.
    Protects against symlink path traversal, oversized files, and hidden directories.
    """

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Path does not exist or is not a directory: {repo_path}")
        self.gitignore_patterns = load_gitignore_patterns(self.repo_path)

    def scan(self) -> ScanSummary:
        start_time = time.perf_counter()
        all_symbols: List[Symbol] = []
        all_edges: List[DependencyEdge] = []
        file_count = 0
        total_unresolved = 0

        # Traverse directory safely (followlinks=False avoids directory link recursion)
        for root, dirs, files in os.walk(self.repo_path, followlinks=False):
            # Prune ignored and hidden directories in-place
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_DIRS
                and not d.startswith(".")
                and not is_path_ignored(
                    os.path.relpath(os.path.join(root, d), self.repo_path),
                    self.gitignore_patterns,
                )
            ]

            for file in sorted(files):
                # Skip hidden files or non-python files
                if file.startswith(".") or not file.endswith(".py"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.repo_path).replace("\\", "/")

                # Skip files matching .gitignore
                if is_path_ignored(rel_path, self.gitignore_patterns):
                    continue

                # Symlink traversal protection: verify realpath stays within repository
                if os.path.islink(full_path):
                    try:
                        resolved_path = os.path.realpath(full_path)
                        # Ensure resolved path is strictly within repo_path
                        common = os.path.commonpath([self.repo_path, resolved_path])
                        if common != self.repo_path:
                            # External symlink target detected - skip for safety
                            continue
                    except Exception:
                        continue

                # Oversized file protection
                try:
                    if os.path.getsize(full_path) > MAX_FILE_SIZE:
                        # Skip oversized files to prevent memory exhaustion
                        continue
                except OSError:
                    continue

                # Safe file read and AST extraction
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    parser = PythonASTParser(rel_path=rel_path, source_code=content)
                    symbols, edges = parser.parse()

                    all_symbols.extend(symbols)
                    all_edges.extend(edges)
                    total_unresolved += parser.unresolved_calls_count
                    file_count += 1
                except Exception:
                    # Continue scanning other files gracefully
                    pass

        # Global edge deduplication: prevent identical (source, target, relation) edges
        seen_edge_keys: Set[Tuple[str, str, str]] = set()
        refined_edges: List[DependencyEdge] = []
        for edge in all_edges:
            key = (edge.source_id, edge.target_id, edge.relation_type.value)
            if key not in seen_edge_keys:
                seen_edge_keys.add(key)
                refined_edges.append(edge)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        commit_sha = get_current_commit_sha(self.repo_path)

        return ScanSummary(
            repo_path=self.repo_path,
            commit_sha=commit_sha,
            file_count=file_count,
            symbol_count=len(all_symbols),
            edge_count=len(refined_edges),
            symbols=all_symbols,
            edges=refined_edges,
            duration_ms=duration_ms,
            unresolved_calls_count=total_unresolved,
        )
