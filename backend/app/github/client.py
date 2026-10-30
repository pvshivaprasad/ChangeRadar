"""Asynchronous GitHub API Client for ChangeRadar.

Handles:
- User profile & token verification
- Authorized repository listing & search
- Pull request listing & details
- Unified diff fetching for PRs and commit ranges
- Idempotent PR comment creation and updates
- Commit status & check run updates
"""
import re
from typing import Any, Dict, List, Optional
import httpx

GITHUB_API_BASE = "https://api.github.com"
BOT_COMMENT_MARKER = "<!-- changeradar-analysis-summary -->"
SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


class GitHubClientError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Safe, typed HTTP client for interacting with the GitHub REST API v3."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ChangeRadar-App/1.0",
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    def _validate_repo_params(self, owner: str, repo: str):
        if not SAFE_NAME_RE.match(owner) or not SAFE_NAME_RE.match(repo):
            raise GitHubClientError("Invalid owner or repository name parameter", status_code=400)

    async def get_user_info(self) -> Dict[str, Any]:
        """Fetches the authenticated GitHub user profile."""
        if not self.access_token:
            raise GitHubClientError("GitHub access token is required", status_code=401)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{GITHUB_API_BASE}/user", headers=self.headers)
            if res.status_code != 200:
                raise GitHubClientError(f"GitHub user request failed: {res.text}", status_code=res.status_code)
            return res.json()

    async def list_repositories(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Lists repositories that the authenticated user has explicit access to."""
        if not self.access_token:
            raise GitHubClientError("GitHub access token is required", status_code=401)

        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {
                "per_page": min(100, max(1, per_page)),
                "sort": "updated",
                "direction": "desc",
            }
            res = await client.get(f"{GITHUB_API_BASE}/user/repos", headers=self.headers, params=params)
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to list GitHub repositories: {res.text}", status_code=res.status_code)

            repos = res.json()
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "owner": r.get("owner", {}).get("login"),
                    "private": r.get("private", False),
                    "html_url": r.get("html_url"),
                    "clone_url": r.get("clone_url"),
                    "default_branch": r.get("default_branch", "main"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at"),
                    "permissions": r.get("permissions", {}),
                }
                for r in repos
            ]

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetches metadata for a specific repository."""
        self._validate_repo_params(owner, repo)
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=self.headers)
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to fetch repository '{owner}/{repo}': {res.text}", status_code=res.status_code)
            r = res.json()
            return {
                "id": r.get("id"),
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "owner": r.get("owner", {}).get("login"),
                "private": r.get("private", False),
                "html_url": r.get("html_url"),
                "clone_url": r.get("clone_url"),
                "default_branch": r.get("default_branch", "main"),
                "description": r.get("description"),
                "language": r.get("language"),
                "size_kb": r.get("size", 0),
                "open_issues_count": r.get("open_issues_count", 0),
            }

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """Lists pull requests for a repository."""
        self._validate_repo_params(owner, repo)
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"state": state, "per_page": 50, "sort": "updated", "direction": "desc"}
            res = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls", headers=self.headers, params=params)
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to list pull requests: {res.text}", status_code=res.status_code)

            prs = res.json()
            return [
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "html_url": pr.get("html_url"),
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "user": pr.get("user", {}).get("login"),
                    "base_ref": pr.get("base", {}).get("ref"),
                    "base_sha": pr.get("base", {}).get("sha"),
                    "head_ref": pr.get("head", {}).get("ref"),
                    "head_sha": pr.get("head", {}).get("sha"),
                    "draft": pr.get("draft", False),
                }
                for pr in prs
            ]

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetches single pull request details."""
        self._validate_repo_params(owner, repo)
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}", headers=self.headers)
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to get PR #{pull_number}: {res.text}", status_code=res.status_code)
            pr = res.json()
            return {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "body": pr.get("body", ""),
                "html_url": pr.get("html_url"),
                "user": pr.get("user", {}).get("login"),
                "base_ref": pr.get("base", {}).get("ref"),
                "base_sha": pr.get("base", {}).get("sha"),
                "head_ref": pr.get("head", {}).get("ref"),
                "head_sha": pr.get("head", {}).get("sha"),
                "changed_files": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
            }

    async def get_pull_request_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """Fetches the unified git diff for a pull request."""
        self._validate_repo_params(owner, repo)
        headers = dict(self.headers)
        headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to fetch diff for PR #{pull_number}: {res.text}", status_code=res.status_code)
            return res.text

    async def get_compare_diff(self, owner: str, repo: str, base_ref: str, head_ref: str) -> str:
        """Fetches unified diff comparing two branches or commit SHAs."""
        self._validate_repo_params(owner, repo)
        headers = dict(self.headers)
        headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/compare/{base_ref}...{head_ref}",
                headers=headers,
            )
            if res.status_code != 200:
                raise GitHubClientError(f"Failed to compare {base_ref}...{head_ref}: {res.text}", status_code=res.status_code)
            return res.text

    async def create_or_update_pr_comment(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        body_markdown: str,
    ) -> Dict[str, Any]:
        """
        Idempotently posts or updates an analysis summary comment on a pull request.
        Searches existing comments for BOT_COMMENT_MARKER to update existing comment,
        preventing annoying comment spam.
        """
        self._validate_repo_params(owner, repo)
        body_with_marker = f"{BOT_COMMENT_MARKER}\n\n{body_markdown}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Search existing issue comments
            comments_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pull_number}/comments"
            list_res = await client.get(comments_url, headers=self.headers)
            if list_res.status_code == 200:
                for c in list_res.json():
                    if BOT_COMMENT_MARKER in c.get("body", ""):
                        comment_id = c.get("id")
                        # Update existing comment
                        patch_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}"
                        update_res = await client.patch(patch_url, headers=self.headers, json={"body": body_with_marker})
                        if update_res.status_code == 200:
                            return {"action": "updated", "comment_id": comment_id, "html_url": update_res.json().get("html_url")}

            # 2. If no existing comment found, post new comment
            post_res = await client.post(comments_url, headers=self.headers, json={"body": body_with_marker})
            if post_res.status_code not in (200, 201):
                raise GitHubClientError(f"Failed to post PR comment: {post_res.text}", status_code=post_res.status_code)
            created = post_res.json()
            return {"action": "created", "comment_id": created.get("id"), "html_url": created.get("html_url")}
