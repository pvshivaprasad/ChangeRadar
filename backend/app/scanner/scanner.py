import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Set

from .models import DependencyEdge, ScanSummary, Symbol
from .parser import PythonASTParser

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
    """

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Path does not exist or is not a directory: {repo_path}")

    def scan(self) -> ScanSummary:
        start_time = time.perf_counter()
        all_symbols: List[Symbol] = []
        all_edges: List[DependencyEdge] = []
        file_count = 0

        # Traverse directory safely
        for root, dirs, files in os.walk(self.repo_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.repo_path)

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()

                        parser = PythonASTParser(rel_path=rel_path, source_code=content)
                        symbols, edges = parser.parse()

                        all_symbols.extend(symbols)
                        all_edges.extend(edges)
                        file_count += 1
                    except Exception as e:
                        # Continue scanning other files if one file fails to read
                        pass

        # Edge target normalization:
        # Match call targets against known symbol IDs
        known_symbol_ids = {s.id for s in all_symbols}
        refined_edges: List[DependencyEdge] = []

        for edge in all_edges:
            # If target exists directly as known symbol, keep it confirmed
            if edge.target_id in known_symbol_ids:
                refined_edges.append(edge)
            else:
                # Check if target is a prefix of a symbol (e.g. module or class name)
                # or keep edge for cross-module provenance
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
        )
