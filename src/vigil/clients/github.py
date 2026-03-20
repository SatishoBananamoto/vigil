"""GitHub API client with rate-limit awareness and caching."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx


@dataclass
class GitHubRepoInfo:
    """Core repository metadata."""

    owner: str
    name: str
    full_name: str
    description: str | None = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    archived: bool = False
    fork: bool = False
    created_at: datetime | None = None
    pushed_at: datetime | None = None
    license: str | None = None
    default_branch: str = "main"


@dataclass
class ContributorInfo:
    """A repository contributor."""

    login: str
    contributions: int


@dataclass
class CommitActivity:
    """Weekly commit activity for a repository."""

    weeks: list[dict] = field(default_factory=list)  # [{week, total, days}, ...]
    total: int = 0


class RateLimitError(Exception):
    """Raised when GitHub rate limit is hit."""

    def __init__(self, reset_at: int):
        self.reset_at = reset_at
        wait = max(0, reset_at - int(time.time()))
        super().__init__(f"GitHub rate limit exceeded. Resets in {wait}s.")


class GitHubClient:
    """Client for the GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: float = 15.0):
        self._token = token or os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=timeout,
        )
        self._cache: dict[str, tuple[float, object]] = {}
        self._cache_ttl = 3600  # 1 hour

    @property
    def authenticated(self) -> bool:
        return self._token is not None

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        """Make a GET request with rate-limit handling and caching."""
        cache_key = f"{path}:{params}"
        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return data

        resp = self._client.get(path, params=params)

        # Check rate limit
        remaining = int(resp.headers.get("x-ratelimit-remaining", 999))
        if resp.status_code == 403 and remaining == 0:
            reset_at = int(resp.headers.get("x-ratelimit-reset", 0))
            raise RateLimitError(reset_at)

        if resp.status_code == 404:
            return None
        if resp.status_code == 202:
            # GitHub is computing data — not ready yet
            return None

        resp.raise_for_status()
        data = resp.json()
        self._cache[cache_key] = (time.time(), data)
        return data

    def rate_limit_status(self) -> dict:
        """Check current rate limit status."""
        resp = self._client.get("/rate_limit")
        resp.raise_for_status()
        core = resp.json().get("resources", {}).get("core", {})
        return {
            "remaining": core.get("remaining", 0),
            "limit": core.get("limit", 0),
            "reset_at": core.get("reset", 0),
        }

    def get_repo(self, owner: str, name: str) -> GitHubRepoInfo | None:
        """Fetch repository metadata."""
        data = self._get(f"/repos/{owner}/{name}")
        if not data or not isinstance(data, dict):
            return None

        return GitHubRepoInfo(
            owner=owner,
            name=name,
            full_name=data.get("full_name", f"{owner}/{name}"),
            description=data.get("description"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            archived=data.get("archived", False),
            fork=data.get("fork", False),
            created_at=_parse_dt(data.get("created_at")),
            pushed_at=_parse_dt(data.get("pushed_at")),
            license=(data.get("license") or {}).get("spdx_id"),
            default_branch=data.get("default_branch", "main"),
        )

    def get_contributors(self, owner: str, name: str, limit: int = 30) -> list[ContributorInfo]:
        """Fetch top contributors."""
        data = self._get(f"/repos/{owner}/{name}/contributors", {"per_page": limit})
        if not data or not isinstance(data, list):
            return []

        return [
            ContributorInfo(login=c["login"], contributions=c.get("contributions", 0))
            for c in data
            if c.get("login")
        ]

    def get_commit_activity(self, owner: str, name: str) -> CommitActivity | None:
        """Fetch weekly commit activity for the last year."""
        data = self._get(f"/repos/{owner}/{name}/stats/commit_activity")
        if not data or not isinstance(data, list):
            return None

        return CommitActivity(
            weeks=data,
            total=sum(w.get("total", 0) for w in data),
        )

    def get_recent_issues(
        self, owner: str, name: str, state: str = "all", limit: int = 30
    ) -> list[dict]:
        """Fetch recent issues (includes PRs)."""
        data = self._get(
            f"/repos/{owner}/{name}/issues",
            {"state": state, "per_page": limit, "sort": "updated"},
        )
        if not data or not isinstance(data, list):
            return []
        return data

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL."""
    url = url.rstrip("/")
    # Handle various formats
    for prefix in ("https://github.com/", "http://github.com/", "git://github.com/"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            parts = path.split("/")
            if len(parts) >= 2:
                repo = parts[1].removesuffix(".git")
                return parts[0], repo
    return None


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
