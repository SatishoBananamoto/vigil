"""PyPI JSON API client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx


@dataclass
class PyPIRelease:
    """A single release of a package."""

    version: str
    upload_time: datetime | None
    yanked: bool = False


@dataclass
class PyPIPackageInfo:
    """Metadata for a PyPI package."""

    name: str
    version: str
    summary: str | None = None
    home_page: str | None = None
    project_urls: dict[str, str] = field(default_factory=dict)
    author: str | None = None
    maintainer: str | None = None
    license: str | None = None
    classifiers: list[str] = field(default_factory=list)
    releases: list[PyPIRelease] = field(default_factory=list)
    requires_dist: list[str] = field(default_factory=list)

    @property
    def repo_url(self) -> str | None:
        """Best guess at source repository URL."""
        # Check project_urls for common keys
        for key in ("Source", "Source Code", "Repository", "GitHub", "Code"):
            if key in self.project_urls:
                return self.project_urls[key]

        # Check Homepage and other URLs if they point to a repo host
        for key in ("Homepage", "Home", "Project", "Documentation"):
            url = self.project_urls.get(key, "")
            if url and ("github.com" in url or "gitlab.com" in url):
                return url

        # Fall back to home_page if it looks like a repo
        if self.home_page and ("github.com" in self.home_page or "gitlab.com" in self.home_page):
            return self.home_page

        return None


class PyPIClient:
    """Client for the PyPI JSON API."""

    BASE_URL = "https://pypi.org/pypi"

    def __init__(self, timeout: float = 15.0):
        self._client = httpx.Client(timeout=timeout)

    def get_package(self, name: str) -> PyPIPackageInfo | None:
        """Fetch package metadata from PyPI. Returns None if not found."""
        url = f"{self.BASE_URL}/{name}/json"
        try:
            resp = self._client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
        except httpx.HTTPError:
            return None

        data = resp.json()
        info = data.get("info", {})

        # Parse releases
        releases = []
        for version, files in data.get("releases", {}).items():
            upload_time = None
            yanked = False
            if files:
                raw = files[0].get("upload_time")
                if raw:
                    try:
                        dt = datetime.fromisoformat(raw)
                        # Ensure timezone-aware (PyPI returns naive UTC)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        upload_time = dt
                    except ValueError:
                        pass
                yanked = files[0].get("yanked", False)
            releases.append(PyPIRelease(
                version=version,
                upload_time=upload_time,
                yanked=yanked,
            ))

        # Sort by upload time (newest first)
        releases.sort(
            key=lambda r: r.upload_time or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return PyPIPackageInfo(
            name=info.get("name", name),
            version=info.get("version", ""),
            summary=info.get("summary"),
            home_page=info.get("home_page"),
            project_urls=info.get("project_urls") or {},
            author=info.get("author"),
            maintainer=info.get("maintainer"),
            license=info.get("license"),
            classifiers=info.get("classifiers", []),
            releases=releases,
            requires_dist=info.get("requires_dist") or [],
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
