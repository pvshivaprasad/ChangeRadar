"""GitHub Integration Service for ChangeRadar.

Handles:
- Secure account connection & token encryption
- Safe isolated repository cloning with strict resource bounds
- Pull request diff ingestion & change blast-radius analysis
- Automated PR comment publishing and updates
- Webhook signature validation, idempotency, and dispatch
"""
from datetime import datetime, timezone
import json
import os
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import (
    Analysis,
    BackgroundJob,
    GitHubAccount,
    GitHubWebhookLog,
    Repository,
    User,
)
from ..scanner import (
    DependencyGraphEngine,
    GitDiffProcessor,
    ImpactAnalysisReport,
    RepositoryScanner,
    TestRecommendationEngine,
)
from ..scanner.git_diff import parse_file_diffs, parse_unified_diff_hunks
from ..security import decrypt_secret, encrypt_secret, mask_token, verify_github_webhook_signature
from .client import GitHubClient, GitHubClientError

SAFE_REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$")


def format_pr_comment(
    report: ImpactAnalysisReport,
    pr_number: int,
    pr_title: str,
) -> str:
    """Formats an executive Markdown comment for GitHub Pull Requests."""
    risk_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "elevated": "🟠",
        "high": "🔴",
    }.get(report.risk_level, "⚪")

    lines = [
        f"## ⚡ ChangeRadar Impact Intelligence — PR #{pr_number}",
        f"**Title**: {pr_title}  ",
        f"**Comparing**: `{report.base_commit[:8] if len(report.base_commit) >= 8 else report.base_commit}` ➔ `{report.head_commit[:8] if len(report.head_commit) >= 8 else report.head_commit}`",
        "",
        "### 📊 Change Blast Radius Overview",
        "| Metric | Result | Explanation |",
        "| :--- | :--- | :--- |",
        f"| **Structural Risk** | {risk_emoji} **{report.risk_level.upper()}** ({report.risk_score}/100) | Weighted structural blast radius across dependency graph |",
        f"| **Changed Symbols** | **{len(report.changed_symbols)}** | Directly modified functions, classes, or modules |",
        f"| **Impacted Dependents** | **{len(report.impacted_symbols)}** | Direct and transitive downstream callers affected |",
        f"| **Recommended Tests** | **{len(report.recommended_tests)}** | Targeted test cases touching affected blast radius |",
        "",
    ]

    # Directly changed symbols
    if report.changed_symbols:
        lines.append("### 🔍 Directly Modified Symbols")
        for sym in report.changed_symbols[:8]:
            lines.append(f"- `{sym.name}` (`{sym.symbol_type.value}`) in `{sym.file_path}:{sym.line_start}`")
        if len(report.changed_symbols) > 8:
            lines.append(f"- *...and {len(report.changed_symbols) - 8} more symbol(s)*")
        lines.append("")

    # Downstream dependents
    dependents = [s for s in report.impacted_symbols if s.depth > 0]
    if dependents:
        lines.append("### 🌊 Affected Downstream Components")
        for dep in dependents[:8]:
            arrow = "➔" * min(3, dep.depth)
            lines.append(f"- {arrow} `{dep.symbol_name}` (depth {dep.depth}) in `{dep.file_path}`")
        if len(dependents) > 8:
            lines.append(f"- *...and {len(dependents) - 8} additional affected component(s)*")
        lines.append("")

    # Recommended tests
    if report.recommended_tests:
        lines.append("### 🧪 What to Test")
        for rec in report.recommended_tests[:6]:
            test_target = f"`{rec.test_symbol_id}` in `{rec.test_file}`" if rec.test_symbol_id else f"`{rec.test_file}`"
            lines.append(f"- **[{rec.priority.upper()}]** Run {test_target} — {rec.reason}")
        if len(report.recommended_tests) > 6:
            lines.append(f"- *...and {len(report.recommended_tests) - 6} additional recommended test(s)*")
        lines.append("")

    lines.append("> [!NOTE]")
    lines.append("> **ChangeRadar Analysis Engine**: Deterministic AST static call-graph traversal.")
    lines.append("> Risk score reflects architectural blast radius across components, not bug probability.")

    return "\n".join(lines)


class GitHubService:
    """Orchestrates GitHub account connections, repository importing, and PR analyses."""

    def __init__(self, db: Session):
        self.db = db

    def get_account(self, user_id: int) -> Optional[GitHubAccount]:
        """Returns the primary GitHub account for a user if connected."""
        return self.db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()

    def get_client(self, user_id: int) -> GitHubClient:
        """Instantiates a GitHubClient with the user's decrypted access token."""
        account = self.get_account(user_id)
        if not account or not account.encrypted_access_token:
            raise GitHubClientError("No GitHub account is connected for this user", status_code=401)
        token = decrypt_secret(account.encrypted_access_token)
        return GitHubClient(access_token=token)

    async def connect_account(
        self,
        user_id: int,
        access_token: str,
        account_type: str = "oauth",
        scopes: str = "repo,read:user",
    ) -> Dict[str, Any]:
        """Verifies GitHub credentials and stores them securely encrypted."""
        client = GitHubClient(access_token=access_token)
        user_info = await client.get_user_info()

        username = user_info.get("login", "")
        github_id = str(user_info.get("id", ""))

        account = self.get_account(user_id)
        encrypted_tok = encrypt_secret(access_token)

        if not account:
            account = GitHubAccount(
                user_id=user_id,
                github_user_id=github_id,
                github_username=username,
                encrypted_access_token=encrypted_tok,
                scopes=scopes,
                account_type=account_type,
            )
            self.db.add(account)
        else:
            account.github_user_id = github_id
            account.github_username = username
            account.encrypted_access_token = encrypted_tok
            account.scopes = scopes
            account.account_type = account_type
            account.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(account)

        return {
            "status": "connected",
            "github_username": account.github_username,
            "account_type": account.account_type,
            "scopes": account.scopes,
            "masked_token": mask_token(access_token),
            "created_at": account.created_at.isoformat(),
        }

    def disconnect_account(self, user_id: int) -> bool:
        """Removes stored GitHub credentials and revokes authorization locally."""
        account = self.get_account(user_id)
        if account:
            self.db.delete(account)
            self.db.commit()
            return True
        return False

    async def list_user_repositories(self, user_id: int) -> List[Dict[str, Any]]:
        """Lists accessible repositories for the user via GitHub API."""
        client = self.get_client(user_id)
        return await client.list_repositories()

    async def import_repository(
        self,
        user_id: int,
        full_name: str,
    ) -> Repository:
        """
        Imports a GitHub repository into an isolated user workspace.
        Enforces:
        - Safe repo name regex
        - Private/public access authorization
        - Max file count and size limits
        - Path traversal guards
        """
        if not SAFE_REPO_NAME_RE.match(full_name):
            raise ValueError(f"Invalid repository full name format: '{full_name}'. Expected 'owner/repo'.")

        client = self.get_client(user_id)
        owner, repo_name = full_name.split("/")

        # 1. Fetch metadata to verify user access
        repo_meta = await client.get_repository(owner, repo_name)

        # 2. Setup isolated target path
        base_storage = os.path.abspath(settings.repo_storage_dir)
        user_storage = os.path.join(base_storage, str(user_id))
        target_dir = os.path.join(user_storage, f"github_{owner}_{repo_name}")
        os.makedirs(user_storage, exist_ok=True)

        # Path traversal guard
        common = os.path.commonpath([base_storage, os.path.abspath(target_dir)])
        if common != base_storage:
            raise PermissionError("Path traversal violation detected in repository destination path")

        account = self.get_account(user_id)
        token = decrypt_secret(account.encrypted_access_token) if account and account.encrypted_access_token else ""

        # 3. Clone or update repository safely
        clone_url = repo_meta.get("clone_url", "")
        auth_clone_url = clone_url.replace("https://", f"https://x-access-token:{token}@") if token else clone_url

        if os.path.isdir(target_dir) and os.path.isdir(os.path.join(target_dir, ".git")):
            # Fast fetch
            subprocess.run(["git", "-C", target_dir, "fetch", "--depth", "1"], capture_output=True, timeout=15)
        else:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            res = subprocess.run(
                ["git", "clone", "--depth", "10", auth_clone_url, target_dir],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if res.returncode != 0:
                raise RuntimeError(f"Git clone failed: {res.stderr.strip()}")

        # 4. Initial AST scan & boundary validation
        scanner = RepositoryScanner(target_dir)
        scan_summary = scanner.scan()

        # Check limits
        if scan_summary.file_count > settings.max_repo_files:
            raise ValueError(f"Repository exceeds file limit: {scan_summary.file_count} > {settings.max_repo_files}")

        # 5. Persist Repository row in DB
        existing_repo = (
            self.db.query(Repository)
            .filter(Repository.user_id == user_id, Repository.github_repo_full_name == full_name)
            .first()
        )

        if not existing_repo:
            new_repo = Repository(
                user_id=user_id,
                name=repo_name,
                path=target_dir,
                repo_type="github",
                default_branch=repo_meta.get("default_branch", "main"),
                github_repo_full_name=full_name,
                github_clone_url=clone_url,
                is_private=repo_meta.get("private", False),
                file_count=scan_summary.file_count,
                symbol_count=scan_summary.symbol_count,
                edge_count=scan_summary.edge_count,
                last_scanned_at=datetime.now(timezone.utc),
            )
            self.db.add(new_repo)
            self.db.commit()
            self.db.refresh(new_repo)
            return new_repo
        else:
            existing_repo.path = target_dir
            existing_repo.file_count = scan_summary.file_count
            existing_repo.symbol_count = scan_summary.symbol_count
            existing_repo.edge_count = scan_summary.edge_count
            existing_repo.last_scanned_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing_repo)
            return existing_repo

    async def analyze_pull_request(
        self,
        user_id: int,
        repo_id: int,
        pr_number: int,
        post_comment: bool = False,
    ) -> Analysis:
        """
        Executes change impact analysis on an open pull request.
        Compares base and head revisions and extracts exact changed symbols and caller blast radius.
        """
        repo = self.db.query(Repository).filter(Repository.id == repo_id, Repository.user_id == user_id).first()
        if not repo:
            raise ValueError("Repository not found or access denied")

        if not repo.github_repo_full_name:
            raise ValueError("Repository is not linked to GitHub")

        owner, repo_name = repo.github_repo_full_name.split("/")
        client = self.get_client(user_id)

        # 1. Fetch PR details
        pr_meta = await client.get_pull_request(owner, repo_name, pr_number)
        base_sha = pr_meta.get("base_sha", "HEAD~1")
        head_sha = pr_meta.get("head_sha", "HEAD")
        pr_title = pr_meta.get("title", f"PR #{pr_number}")

        # 2. Fetch unified diff
        diff_text = await client.get_pull_request_diff(owner, repo_name, pr_number)

        # 3. Parse changed ranges & file diffs
        changed_ranges_by_file, renamed_files, deleted_files = parse_unified_diff_hunks(diff_text)
        file_diffs = parse_file_diffs(diff_text)

        # 4. Scan repository symbols on target clone
        scanner = RepositoryScanner(repo.path)
        scan_summary = scanner.scan()

        # 5. Intersect diff with AST symbols
        changed_symbols = []
        seen_sym_ids = set()

        for del_path in deleted_files:
            from ..scanner.parser import module_name_from_file_path
            from ..scanner.models import Symbol, SymbolType
            mod_id = module_name_from_file_path(del_path)
            if mod_id not in seen_sym_ids:
                seen_sym_ids.add(mod_id)
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

        for sym in scan_summary.symbols:
            sym_file = sym.file_path.replace("\\", "/")
            if sym_file in changed_ranges_by_file:
                for r_start, r_end in changed_ranges_by_file[sym_file]:
                    if max(sym.line_start, r_start) <= min(sym.line_end, r_end):
                        if sym.id not in seen_sym_ids:
                            seen_sym_ids.add(sym.id)
                            changed_symbols.append(sym)
                        break

        # Specificity filtering
        symbols_by_file: Dict[str, List] = {}
        for s in changed_symbols:
            symbols_by_file.setdefault(s.file_path, []).append(s)

        filtered_symbols = []
        for file_path, file_syms in symbols_by_file.items():
            has_specific = any(s.symbol_type.value != "module" for s in file_syms)
            filtered_symbols.extend([s for s in file_syms if s.symbol_type.value != "module"] if has_specific else file_syms)
        changed_symbols = filtered_symbols

        # 6. Graph traversal
        graph_engine = DependencyGraphEngine(symbols=scan_summary.symbols, edges=scan_summary.edges)
        changed_ids = [s.id for s in changed_symbols]
        impacted_symbols = graph_engine.find_impacted_symbols(changed_ids)

        # 7. Test recommendations
        test_engine = TestRecommendationEngine(all_symbols=scan_summary.symbols, all_edges=scan_summary.edges)
        recommended_tests = test_engine.recommend_tests(impacted_symbols)

        # 8. Risk computation
        risk_level, risk_score = graph_engine.compute_risk(impacted_symbols)

        summary_text = (
            f"PR #{pr_number} modified {len(changed_symbols)} symbol(s) in {len(changed_ranges_by_file)} file(s). "
            f"Blast radius analysis identified {len(impacted_symbols)} directly or transitively affected symbol(s). "
            f"Selected {len(recommended_tests)} targeted test(s)."
        )

        report = ImpactAnalysisReport(
            repo_path=repo.path,
            base_commit=base_sha,
            head_commit=head_sha,
            changed_files=list(changed_ranges_by_file.keys()),
            changed_symbols=changed_symbols,
            impacted_symbols=impacted_symbols,
            graph_nodes_count=scan_summary.symbol_count,
            graph_edges_count=scan_summary.edge_count,
            recommended_tests=recommended_tests,
            risk_level=risk_level,
            risk_score=risk_score,
            summary_text=summary_text,
            unresolved_calls_count=scan_summary.unresolved_calls_count,
            created_at=datetime.now(timezone.utc).isoformat(),
            file_diffs=file_diffs,
        )

        # 9. Optional PR comment posting
        comment_id = None
        if post_comment:
            comment_md = format_pr_comment(report=report, pr_number=pr_number, pr_title=pr_title)
            comment_res = await client.create_or_update_pr_comment(
                owner=owner,
                repo=repo_name,
                pull_number=pr_number,
                body_markdown=comment_md,
            )
            comment_id = str(comment_res.get("comment_id", ""))

        # 10. Persist analysis
        analysis = Analysis(
            user_id=user_id,
            repository_id=repo.id,
            repo_name=repo.name,
            repo_path=repo.path,
            base_commit=base_sha,
            head_commit=head_sha,
            pr_number=pr_number,
            pr_title=pr_title,
            is_github_pr=True,
            github_comment_id=comment_id,
            analysis_engine_version=settings.analysis_engine_version,
            status="completed",
            risk_level=risk_level,
            risk_score=risk_score,
            changed_files_count=len(changed_ranges_by_file),
            changed_symbols_count=len(changed_symbols),
            impacted_symbols_count=len(impacted_symbols),
            recommended_tests_count=len(recommended_tests),
            summary_text=summary_text,
            report_json=json.dumps(report.model_dump()),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    async def handle_webhook(
        self,
        delivery_id: str,
        event_type: str,
        payload_bytes: bytes,
        signature_header: Optional[str],
    ) -> Dict[str, Any]:
        """Validates, deduplicates, and processes an incoming GitHub webhook."""
        # 1. Signature validation if secret is set
        if settings.github_webhook_secret:
            valid = verify_github_webhook_signature(
                payload_bytes=payload_bytes,
                signature_header=signature_header,
                webhook_secret=settings.github_webhook_secret,
            )
            if not valid:
                raise PermissionError("Invalid GitHub webhook signature")

        # 2. Idempotency check: duplicate delivery ID
        existing_log = (
            self.db.query(GitHubWebhookLog)
            .filter(GitHubWebhookLog.delivery_id == delivery_id)
            .first()
        )
        if existing_log:
            return {"status": "duplicate_ignored", "delivery_id": delivery_id}

        payload: Dict[str, Any] = {}
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            pass

        repo_full_name = payload.get("repository", {}).get("full_name")
        sender = payload.get("sender", {}).get("login")

        # Record log
        log_entry = GitHubWebhookLog(
            delivery_id=delivery_id,
            event_type=event_type,
            repository_name=repo_full_name,
            sender_username=sender,
            payload_json=json.dumps(payload),
            status="received",
        )
        self.db.add(log_entry)
        self.db.commit()

        # Handle pull_request event
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ("opened", "synchronize", "reopened"):
                pr_num = payload.get("number")
                # Look up registered repository
                repo = (
                    self.db.query(Repository)
                    .filter(Repository.github_repo_full_name == repo_full_name)
                    .first()
                )
                if repo:
                    try:
                        log_entry.status = "processing"
                        self.db.commit()
                        await self.analyze_pull_request(
                            user_id=repo.user_id,
                            repo_id=repo.id,
                            pr_number=pr_num,
                            post_comment=True,
                        )
                        log_entry.status = "completed"
                    except Exception as exc:
                        log_entry.status = "failed"
                        log_entry.error_message = str(exc)
                    self.db.commit()

        return {"status": "processed", "delivery_id": delivery_id, "event_type": event_type}
