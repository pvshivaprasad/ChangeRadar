"""Automated test suite validating Git diff edge cases:
- Added files
- Deleted files
- Modified functions
- Multiple changed functions
- Renamed files
- Empty diffs
- Malicious revision injection prevention
"""
import pytest
from app.scanner.git_diff import GitDiffProcessor, parse_file_diffs, parse_unified_diff_hunks
from app.scanner.models import Symbol, SymbolType


def test_empty_diff():
    diff_text = ""
    ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    assert ranges == {}
    assert renamed == {}
    assert deleted == set()


def test_added_files_hunk_parsing():
    diff_text = """diff --git a/new_module.py b/new_module.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_module.py
@@ -0,0 +1,25 @@
+class NewClass:
+    def new_method(self):
+        return True
+"""
    ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    assert "new_module.py" in ranges
    assert ranges["new_module.py"] == [(1, 25)]
    assert deleted == set()
    assert renamed == {}


def test_deleted_files_hunk_parsing():
    diff_text = """diff --git a/obsolete/old_service.py b/obsolete/old_service.py
deleted file mode 100644
index 1234567..0000000
--- a/obsolete/old_service.py
+++ /dev/null
@@ -1,30 +0,0 @@
-class ObsoleteService:
-    pass
"""
    ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    assert "obsolete/old_service.py" in deleted
    assert "obsolete/old_service.py" in ranges


def test_renamed_files_hunk_parsing():
    diff_text = """diff --git a/old_dir/util.py b/new_dir/util.py
similarity index 100%
rename from old_dir/util.py
rename to new_dir/util.py
"""
    ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    assert "new_dir/util.py" in renamed
    assert renamed["new_dir/util.py"] == "old_dir/util.py"
    assert "new_dir/util.py" in ranges


def test_modified_function_and_multiple_hunks():
    diff_text = """diff --git a/services/core.py b/services/core.py
index abc..def 100644
--- a/services/core.py
+++ b/services/core.py
@@ -10,3 +10,4 @@ def first_function():
+    pass
@@ -50,5 +51,5 @@ def second_function():
-    return 1
+    return 2
"""
    ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    assert "services/core.py" in ranges
    assert len(ranges["services/core.py"]) == 2
    assert ranges["services/core.py"][0] == (10, 13)
    assert ranges["services/core.py"][1] == (51, 55)


def test_symbol_intersection_with_multiple_changed_functions(tmp_path):
    processor = GitDiffProcessor(str(tmp_path))

    symbols = [
        Symbol(
            id="services.core.first_function",
            name="first_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="services/core.py",
            line_start=8,
            line_end=15,
        ),
        Symbol(
            id="services.core.untouched_function",
            name="untouched_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="services/core.py",
            line_start=20,
            line_end=35,
        ),
        Symbol(
            id="services.core.second_function",
            name="second_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="services/core.py",
            line_start=48,
            line_end=60,
        ),
    ]

    diff_text = """diff --git a/services/core.py b/services/core.py
index abc..def 100644
--- a/services/core.py
+++ b/services/core.py
@@ -10,3 +10,4 @@
+    pass
@@ -50,5 +51,5 @@
+    return 2
"""
    # Parse diff and intersect
    changed_ranges, renamed, deleted = parse_unified_diff_hunks(diff_text)
    changed_symbols = []
    for sym in symbols:
        for r_start, r_end in changed_ranges["services/core.py"]:
            if max(sym.line_start, r_start) <= min(sym.line_end, r_end):
                changed_symbols.append(sym)
                break

    changed_names = [s.name for s in changed_symbols]
    assert "first_function" in changed_names
    assert "second_function" in changed_names
    assert "untouched_function" not in changed_names


def test_revision_injection_rejection(tmp_path):
    processor = GitDiffProcessor(str(tmp_path))

    # Reject options starting with hyphen
    with pytest.raises(ValueError, match="Invalid base commit"):
        processor.get_changed_symbols(base_commit="--output=/tmp/evil", head_commit="HEAD", symbols=[])

    with pytest.raises(ValueError, match="Invalid head commit"):
        processor.get_changed_symbols(base_commit="HEAD~1", head_commit="; rm -rf /", symbols=[])


def test_parse_file_diffs_all_change_types():
    diff_text = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,5 @@
+def brand_new():
+    return True
diff --git a/modified.py b/modified.py
index abc..def 100644
--- a/modified.py
+++ b/modified.py
@@ -10,3 +10,4 @@
-    old_call()
+    new_call()
+    extra_line()
diff --git a/obsolete.py b/obsolete.py
deleted file mode 100644
--- a/obsolete.py
+++ /dev/null
@@ -1,5 +0,0 @@
-def gone():
-    pass
diff --git a/old_name.py b/renamed.py
similarity index 95%
rename from old_name.py
rename to renamed.py
@@ -1,2 +1,2 @@
"""
    diffs = parse_file_diffs(diff_text)
    assert len(diffs) == 4

    # 1. Added
    added = next(d for d in diffs if d.file_path == "new_file.py")
    assert added.change_type == "added"
    assert added.additions == 2
    assert added.deletions == 0

    # 2. Modified
    mod = next(d for d in diffs if d.file_path == "modified.py")
    assert mod.change_type == "modified"
    assert mod.additions == 2
    assert mod.deletions == 1

    # 3. Deleted
    del_file = next(d for d in diffs if d.file_path == "obsolete.py")
    assert del_file.change_type == "deleted"
    assert del_file.deletions == 2

    # 4. Renamed
    ren = next(d for d in diffs if d.file_path == "renamed.py")
    assert ren.change_type == "renamed"
    assert ren.old_path == "old_name.py"
