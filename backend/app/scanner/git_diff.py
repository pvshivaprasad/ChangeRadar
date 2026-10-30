import os
import re
import subprocess
from typing import Dict, List, Set, Tuple

from .models import Symbol, SymbolType
from .parser import module_name_from_file_path

# Strict regex to ensure git revision parameters contain only valid ref characters
REVISION_RE = re.compile(r"^[a-zA-Z0-9_\-\.\/\^~@]+$")


def parse_unified_diff_hunks(
    diff_output: str,
) -> Tuple[Dict[str, List[Tuple[int, int]]], Dict[str, str], Set[str]]:
    """
    Parses git diff output and returns:
    1. changed_ranges: { rel_file_path: [(start_line, end_line), ...] }
    2. renamed_files: { new_rel_path: old_rel_path }
    3. deleted_files: { old_rel_path }
    """
    changed_ranges: Dict[str, List[Tuple[int, int]]] = {}
    renamed_files: Dict[str, str] = {}
    deleted_files: Set[str] = set()

    current_file: str | None = None
    old_file_path: str | None = None

    diff_file_re = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
    hunk_header_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for line in diff_output.splitlines():
        file_match = diff_file_re.match(line)
        if file_match:
            old_file_path = file_match.group(1).replace("\\", "/")
            raw_path = file_match.group(2).replace("\\", "/")
            current_file = raw_path

            if old_file_path != raw_path:
                renamed_files[raw_path] = old_file_path

            if current_file not in changed_ranges:
                changed_ranges[current_file] = []
            continue

        if line.startswith("deleted file mode") or line.startswith("+++ /dev/null"):
            if old_file_path:
                deleted_files.add(old_file_path)
            continue

        if current_file:
            hunk_match = hunk_header_re.match(line)
            if hunk_match:
                start_line = int(hunk_match.group(1))
                line_count = int(hunk_match.group(2)) if hunk_match.group(2) is not None else 1
                if line_count == 0:
                    end_line = start_line
                else:
                    end_line = start_line + line_count - 1

                changed_ranges[current_file].append((start_line, end_line))

    return changed_ranges, renamed_files, deleted_files


class GitDiffProcessor:
    """
    Runs git diff between two commit SHAs/refs, parses modified line ranges,
    and identifies exactly which AST symbols are altered.
    Handles added files, deleted files, modified functions, multiple changed functions,
    renamed files, and empty diffs.
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
        # Validate commit references to prevent command injection
        if not REVISION_RE.match(base_commit) or base_commit.startswith("-"):
            raise ValueError(f"Invalid base commit ref: {base_commit}")
        if not REVISION_RE.match(head_commit) or head_commit.startswith("-"):
            raise ValueError(f"Invalid head commit ref: {head_commit}")

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

        # If diff is empty, return empty results immediately
        if not diff_text or not diff_text.strip():
            return [], []

        changed_ranges_by_file, renamed_files, deleted_files = parse_unified_diff_hunks(diff_text)
        changed_files = list(changed_ranges_by_file.keys())

        changed_symbols: List[Symbol] = []
        seen_symbol_ids: Set[str] = set()

        # 1. Process deleted files (synthesize module-level symbol for caller impact tracing)
        for del_path in deleted_files:
            mod_id = module_name_from_file_path(del_path)
            if mod_id not in seen_symbol_ids:
                seen_symbol_ids.add(mod_id)
                changed_symbols.append(
                    Symbol(
                        id=mod_id,
                        name=os.path.basename(del_path).replace(".py", ""),
                        symbol_type=SymbolType.MODULE,
                        file_path=del_path,
                        line_start=1,
                        line_end=1,
                        docstring=f"Deleted module: {del_path}",
                    )
                )

        # 2. Intersect with scanned symbols in HEAD
        for sym in symbols:
            sym_file = sym.file_path.replace("\\", "/")

            # If file was renamed, all symbols in the new file are marked as changed
            if sym_file in renamed_files and sym.id not in seen_symbol_ids:
                seen_symbol_ids.add(sym.id)
                changed_symbols.append(sym)
                continue

            if sym_file in changed_ranges_by_file:
                ranges = changed_ranges_by_file[sym_file]
                for r_start, r_end in ranges:
                    # Check interval overlap: max(sym.line_start, r_start) <= min(sym.line_end, r_end)
                    if max(sym.line_start, r_start) <= min(sym.line_end, r_end):
                        if sym.id not in seen_symbol_ids:
                            seen_symbol_ids.add(sym.id)
                            changed_symbols.append(sym)
                        break

        # Filter out module symbol if more specific classes/functions inside it were detected
        has_specific = any(s.symbol_type.value in ("function", "method", "class") for s in changed_symbols)
        if has_specific:
            changed_symbols = [s for s in changed_symbols if s.symbol_type.value != "module"]

        return changed_files, changed_symbols
