import os
import re
import subprocess
from typing import Dict, List, Set, Tuple

from .models import Symbol


def parse_unified_diff_hunks(diff_output: str) -> Dict[str, List[Tuple[int, int]]]:
    """
    Parses git diff output and returns a dictionary of:
    { rel_file_path: [(start_line, end_line), ...] }
    representing added or modified line ranges in the HEAD revision.
    """
    changed_ranges: Dict[str, List[Tuple[int, int]]] = {}
    current_file: str | None = None

    # Matches diff --git a/path/to/file.py b/path/to/file.py
    diff_file_re = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
    # Matches @@ -old_start,old_len +new_start,new_len @@
    hunk_header_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for line in diff_output.splitlines():
        file_match = diff_file_re.match(line)
        if file_match:
            # We track the new (b/) path
            raw_path = file_match.group(2).replace("\\", "/")
            current_file = raw_path
            if current_file not in changed_ranges:
                changed_ranges[current_file] = []
            continue

        if current_file:
            hunk_match = hunk_header_re.match(line)
            if hunk_match:
                start_line = int(hunk_match.group(1))
                line_count = int(hunk_match.group(2)) if hunk_match.group(2) is not None else 1
                if line_count == 0:
                    # Deletion only at this exact point
                    end_line = start_line
                else:
                    end_line = start_line + line_count - 1

                changed_ranges[current_file].append((start_line, end_line))

    return changed_ranges


class GitDiffProcessor:
    """
    Runs git diff between two commit SHAs/refs, parses modified line ranges,
    and identifies exactly which AST symbols are altered.
    """

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Path does not exist: {repo_path}")

    def get_changed_symbols(
        self,
        base_commit: str,
        head_commit: str,
        symbols: List[Symbol],
    ) -> Tuple[List[str], List[Symbol]]:
        """
        Runs git diff between base_commit and head_commit,
        and intersects changed line ranges with known AST symbol boundaries.
        Returns: (changed_file_paths, changed_symbols)
        """
        cmd = ["git", "-C", self.repo_path, "diff", "-U0", base_commit, head_commit]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode != 0:
                raise RuntimeError(f"Git diff failed: {res.stderr.strip()}")
            diff_text = res.stdout
        except Exception as exc:
            raise RuntimeError(f"Failed to execute git diff: {exc}")

        changed_ranges_by_file = parse_unified_diff_hunks(diff_text)
        changed_files = list(changed_ranges_by_file.keys())

        # Intersect with symbols
        changed_symbols: List[Symbol] = []
        seen_symbol_ids: Set[str] = set()

        for sym in symbols:
            # Normalize file paths
            sym_file = sym.file_path.replace("\\", "/")
            if sym_file in changed_ranges_by_file:
                ranges = changed_ranges_by_file[sym_file]
                for r_start, r_end in ranges:
                    # Check overlap: max(sym.line_start, r_start) <= min(sym.line_end, r_end)
                    if max(sym.line_start, r_start) <= min(sym.line_end, r_end):
                        if sym.id not in seen_symbol_ids:
                            # Prefer functions and methods over broad module-level symbol
                            seen_symbol_ids.add(sym.id)
                            changed_symbols.append(sym)
                        break

        # If a function or method was modified, we prefer the most specific symbol
        # Filter out module symbol if more specific classes/functions inside it were detected
        has_specific = any(s.symbol_type.value in ("function", "method", "class") for s in changed_symbols)
        if has_specific:
            changed_symbols = [s for s in changed_symbols if s.symbol_type.value != "module"]

        return changed_files, changed_symbols
