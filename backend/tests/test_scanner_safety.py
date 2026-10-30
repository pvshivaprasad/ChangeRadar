"""Automated test suite verifying RepositoryScanner safety:
- .gitignore handling
- Hidden folders and hidden files
- Symlinks and path traversal
- Oversized files (> 2MB cap)
- Syntax errors and null bytes
- Empty repositories
"""
import os
import pytest
from app.scanner.parser import PythonASTParser
from app.scanner.scanner import RepositoryScanner, is_path_ignored, load_gitignore_patterns


def test_empty_repository(tmp_path):
    scanner = RepositoryScanner(str(tmp_path))
    summary = scanner.scan()

    assert summary.file_count == 0
    assert summary.symbol_count == 0
    assert summary.edge_count == 0
    assert summary.symbols == []
    assert summary.edges == []


def test_gitignore_handling(tmp_path):
    # Create files
    keep_file = tmp_path / "app.py"
    keep_file.write_text("def keep(): pass", encoding="utf-8")

    ignored_dir = tmp_path / "generated"
    ignored_dir.mkdir()
    (ignored_dir / "gen.py").write_text("def gen(): pass", encoding="utf-8")

    ignored_file = tmp_path / "debug.py"
    ignored_file.write_text("def debug(): pass", encoding="utf-8")

    # Create .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("generated/\ndebug.py\n*.tmp.py\n# Comment\n", encoding="utf-8")

    scanner = RepositoryScanner(str(tmp_path))
    summary = scanner.scan()

    scanned_files = [s.file_path.replace("\\", "/") for s in summary.symbols]
    assert any("app.py" in f for f in scanned_files)
    assert not any("generated" in f for f in scanned_files)
    assert not any("debug.py" in f for f in scanned_files)


def test_hidden_folders_and_files_skipped(tmp_path):
    # Regular file
    (tmp_path / "main.py").write_text("def run(): pass", encoding="utf-8")

    # Hidden folder
    hidden_dir = tmp_path / ".cache_dir"
    hidden_dir.mkdir()
    (hidden_dir / "internal.py").write_text("def secret(): pass", encoding="utf-8")

    # Hidden file
    (tmp_path / ".hidden_script.py").write_text("def hidden(): pass", encoding="utf-8")

    scanner = RepositoryScanner(str(tmp_path))
    summary = scanner.scan()

    scanned_files = [s.file_path.replace("\\", "/") for s in summary.symbols]
    assert any("main.py" in f for f in scanned_files)
    assert not any(".cache_dir" in f for f in scanned_files)
    assert not any(".hidden_script.py" in f for f in scanned_files)


def test_oversized_file_skipped(tmp_path):
    # Create normal file
    (tmp_path / "normal.py").write_text("def normal(): pass", encoding="utf-8")

    # Create an oversized file > 2MB
    oversized = tmp_path / "huge_data.py"
    with open(oversized, "wb") as f:
        # Write 2.5 MB of dummy Python comments
        f.write(b"# " + b"X" * (2500 * 1024) + b"\n")

    scanner = RepositoryScanner(str(tmp_path))
    summary = scanner.scan()

    scanned_files = [s.file_path.replace("\\", "/") for s in summary.symbols]
    assert any("normal.py" in f for f in scanned_files)
    assert not any("huge_data.py" in f for f in scanned_files)


def test_syntax_errors_and_null_bytes_handled_gracefully(tmp_path):
    # Valid file
    (tmp_path / "good.py").write_text("def good_func(): return 42", encoding="utf-8")

    # Syntax error file
    (tmp_path / "broken_syntax.py").write_text("def broken(: syntax error !!!", encoding="utf-8")

    # File with null bytes
    (tmp_path / "null_bytes.py").write_bytes(b"def null_func():\x00\x01\x02 pass")

    # File with non-utf8 Latin1 chars
    (tmp_path / "latin.py").write_bytes("def latin(): return 'café'".encode("latin-1"))

    scanner = RepositoryScanner(str(tmp_path))
    summary = scanner.scan()

    scanned_names = [s.name for s in summary.symbols]
    assert "good_func" in scanned_names
    # Parser gracefully handled broken files without crashing the scanner


def test_symlink_external_target_protection(tmp_path):
    repo_dir = tmp_path / "my_repo"
    repo_dir.mkdir()
    (repo_dir / "repo_file.py").write_text("def safe(): pass", encoding="utf-8")

    # Outside file
    outside_dir = tmp_path / "sensitive"
    outside_dir.mkdir()
    outside_file = outside_dir / "external_secret.py"
    outside_file.write_text("SECRET_KEY = 'super_secret'", encoding="utf-8")

    # Try creating symlink inside repo pointing to outside file if OS allows
    symlink_path = repo_dir / "link_to_secret.py"
    try:
        os.symlink(str(outside_file), str(symlink_path))
    except (OSError, NotImplementedError):
        # On Windows without developer mode/admin rights, symlink creation may require privilege
        pytest.skip("Symlink creation not permitted by current OS privileges")

    scanner = RepositoryScanner(str(repo_dir))
    summary = scanner.scan()

    scanned_files = [s.file_path.replace("\\", "/") for s in summary.symbols]
    assert any("repo_file.py" in f for f in scanned_files)
    assert not any("link_to_secret.py" in f for f in scanned_files)
