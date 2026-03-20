"""Base protocol for health signal analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from vigil.clients.github import GitHubClient, GitHubRepoInfo
from vigil.clients.pypi import PyPIClient, PyPIPackageInfo
from vigil.models import Signal


class AnalyzerContext:
    """Shared context passed to all analyzers during a scan."""

    def __init__(self, github: GitHubClient, pypi: PyPIClient):
        self.github = github
        self.pypi = pypi


class Analyzer(ABC):
    """Base class for health signal analyzers.

    Each analyzer extracts one or more signals from a specific dimension
    of dependency health.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        ...

    @abstractmethod
    def analyze(
        self,
        package: str,
        ctx: AnalyzerContext,
        pypi_info: PyPIPackageInfo | None = None,
        repo_info: GitHubRepoInfo | None = None,
    ) -> list[Signal]:
        """Extract health signals for a package.

        Returns an empty list if this analyzer cannot assess the package
        (e.g., no GitHub repo found for a repo-dependent analyzer).
        """
        ...
