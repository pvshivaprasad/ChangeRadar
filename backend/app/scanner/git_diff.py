import os
import re
import subprocess
from typing import Dict, List, Set, Tuple

from .models import FileDiff, Symbol, SymbolType
from .parser import module_name_from_file_path

# Strict regex to ensure git revision parameters contain only valid ref characters
REVISION_RE = re.compile(r"^[a-zA-Z0-9_\-\.\/\^~@]+$")


def parse_file_diffs(diff_output: str) -> List[FileDiff]:
    """
    Parses unified git diff output into structured FileDiff items
    categorizing added, modified, deleted, and renamed files,
    along with additions count, deletions count, and unified diff hunks.
    """
    if not diff_output or not diff_output.strip():
        return []

    file_diffs: List[FileDiff] = []
    lines = diff_output.splitlines()
    i = 0
    diff_file_re = re.compile(r"^diff --git a/(.*?) b/(.*?)$")

    while i < len(lines):
        line = lines[i]
        match = diff_file_re.match(line)
        if match:
            old_path = match.group(1).replace("\\", "/")
            new_path = match.group(2).replace("\\", "/")

            section_lines = [line]
            i += 1
            while i < len(lines) and not diff_file_re.match(lines[i]):
                section_lines.append(lines[i])
                i += 1

            is_new = any(l.startswith("new file mode") or l.startswith("--- /dev/null") for l in section_lines)
            is_deleted = any(l.startswith("deleted file mode") or l.startswith("+++ /dev/null") for l in section_lines)
            is_renamed = any(l.startswith("similarity index") or l.startswith("rename from") for l in section_lines) or (old_path != new_path and not is_new and not is_deleted)

            if is_new:
                change_type = "added"
                target_path = new_path
            elif is_deleted:
                change_type = "deleted"
                target_path = old_path
            elif is_renamed:
                change_type = "renamed"
                target_path = new_path
            else:
                change_type = "modified"
                target_path = new_path

            additions = sum(1 for l in section_lines if l.startswith("+") and not l.startswith("+++"))
            deletions = sum(1 for l in section_lines if l.startswith("-") and not l.startswith("---"))

            # Extract unified diff hunks starting from the first @@
            hunk_start = -1
            for idx, l in enumerate(section_lines):
                if l.startswith("@@"):
                    hunk_start = idx
                    break
            diff_content = "\n".join(section_lines[hunk_start:]) if hunk_start != -1 else "\n".join(section_lines)

            file_diffs.append(
                FileDiff(
                    file_path=target_path,
                    change_type=change_type,
                    old_path=old_path if is_renamed else None,
                    diff_content=diff_content,
                    additions=additions,
                    deletions=deletions,
                )
            )
        else:
            i += 1

    return file_diffs


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

        # 3. Hierarchical specificity filtering (per-file)
        symbols_by_file: Dict[str, List[Symbol]] = {}
        for s in changed_symbols:
            symbols_by_file.setdefault(s.file_path, []).append(s)

        filtered_symbols: List[Symbol] = []
        for file_path, file_syms in symbols_by_file.items():
            # If any function, method, or class was modified in this file,
            # drop the module-level symbol for this specific file.
            has_specific = any(s.symbol_type != SymbolType.MODULE for s in file_syms)
            candidates = [s for s in file_syms if s.symbol_type != SymbolType.MODULE] if has_specific else file_syms

            # Method vs Class specificity:
            # If a class and its methods are both candidates in this file:
            # Check if all changed ranges overlapping with the class fall strictly within its child methods.
            classes = [s for s in candidates if s.symbol_type == SymbolType.CLASS]
            methods = [s for s in candidates if s.symbol_type == SymbolType.METHOD]
            ranges = changed_ranges_by_file.get(file_path, [])

            classes_to_remove: Set[str] = set()
            for cls_sym in classes:
                child_methods = [m for m in methods if m.parent_id == cls_sym.id or m.id.startswith(f"{cls_sym.id}.")]
                if child_methods:
                    all_in_methods = True
                    has_overlap = False
                    for r_start, r_end in ranges:
                        if max(cls_sym.line_start, r_start) <= min(cls_sym.line_end, r_end):
                            has_overlap = True
                            in_any_method = any(
                                max(m.line_start, r_start) <= min(m.line_end, r_end)
                                for m in child_methods
                            )
                            if not in_any_method:
                                all_in_methods = False
                                break
                    if has_overlap and all_in_methods:
                        classes_to_remove.add(cls_sym.id)

            candidates = [s for s in candidates if s.id not in classes_to_remove]
            filtered_symbols.extend(candidates)

        changed_symbols = filtered_symbols

        return changed_files, changed_symbols

    def get_file_diffs(self, base_commit: str, head_commit: str) -> List[FileDiff]:
        """
        Runs git diff -U3 between base_commit and head_commit,
        and returns structured file diffs with hunks for visual inspection.
        """
        if not REVISION_RE.match(base_commit) or base_commit.startswith("-"):
            raise ValueError(f"Invalid base commit ref: {base_commit}")
        if not REVISION_RE.match(head_commit) or head_commit.startswith("-"):
            raise ValueError(f"Invalid head commit ref: {head_commit}")

        cmd = ["git", "-C", self.repo_path, "diff", "-U3", base_commit, head_commit]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode != 0:
                return []
            return parse_file_diffs(res.stdout)
        except Exception:
            return []
