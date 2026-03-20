"""Security posture analysis — CI/CD signals, security policy, vulnerability indicators."""

from __future__ import annotations

from vigil.analyzers.base import Analyzer, AnalyzerContext
from vigil.clients.github import GitHubClient, GitHubRepoInfo
from vigil.clients.pypi import PyPIPackageInfo
from vigil.models import Signal, SignalCategory


class SecurityAnalyzer(Analyzer):
    """Analyzes security-related signals for a project."""

    @property
    def name(self) -> str:
        return "security"

    def analyze(
        self,
        package: str,
        ctx: AnalyzerContext,
        pypi_info: PyPIPackageInfo | None = None,
        repo_info: GitHubRepoInfo | None = None,
    ) -> list[Signal]:
        signals = []

        if repo_info and not repo_info.archived:
            owner, repo = repo_info.owner, repo_info.name

            # 1. Security policy presence
            signals.append(self._security_policy(ctx.github, owner, repo))

            # 2. License clarity
            signals.append(self._license_signal(repo_info, pypi_info))

            # 3. Archive/fork risk
            if repo_info.fork:
                signals.append(Signal(
                    name="is_fork",
                    category=SignalCategory.SECURITY,
                    value=0.4,
                    confidence=0.6,
                    detail="Package source is a fork — may diverge from upstream.",
                ))

        # 4. PyPI-level signals
        if pypi_info:
            signals.append(self._development_status(pypi_info))
            signals.append(self._yanked_releases(pypi_info))

        return signals

    def _security_policy(self, github: GitHubClient, owner: str, repo: str) -> Signal:
        """Check for SECURITY.md or security policy."""
        # Use community profile endpoint — single call, multiple signals
        data = github._get(f"/repos/{owner}/{repo}/community/profile")
        if not data or not isinstance(data, dict):
            return Signal(
                name="security_policy",
                category=SignalCategory.SECURITY,
                value=0.5,
                confidence=0.3,
                detail="Could not check community profile.",
            )

        files = data.get("files", {})
        has_security = files.get("security") is not None
        has_contributing = files.get("contributing") is not None
        has_code_of_conduct = files.get("code_of_conduct") is not None

        present = []
        if has_security:
            present.append("SECURITY.md")
        if has_contributing:
            present.append("CONTRIBUTING.md")
        if has_code_of_conduct:
            present.append("Code of Conduct")

        if has_security:
            value = 0.9
            detail = f"Security policy present. Also: {', '.join(present)}."
        elif has_contributing:
            value = 0.6
            detail = f"No security policy, but has: {', '.join(present)}."
        else:
            value = 0.3
            detail = "No security policy or contributing guidelines."

        return Signal(
            name="security_policy",
            category=SignalCategory.SECURITY,
            value=value,
            confidence=0.6,
            detail=detail,
            raw_data={
                "security": has_security,
                "contributing": has_contributing,
                "code_of_conduct": has_code_of_conduct,
            },
        )

    def _license_signal(self, repo: GitHubRepoInfo, pypi_info: PyPIPackageInfo | None) -> Signal:
        """Is the license clear and standard?"""
        license_id = repo.license
        pypi_license = pypi_info.license if pypi_info else None

        if not license_id or license_id == "NOASSERTION":
            if pypi_license and pypi_license.strip():
                value = 0.5
                detail = f"License on PyPI ({pypi_license}) but not detected on GitHub."
            else:
                value = 0.2
                detail = "No license detected — legal risk for dependents."
        elif license_id in ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"):
            value = 0.95
            detail = f"Permissive license: {license_id}."
        elif license_id in ("GPL-2.0-only", "GPL-3.0-only", "AGPL-3.0-only", "LGPL-2.1-only", "LGPL-3.0-only"):
            value = 0.7
            detail = f"Copyleft license: {license_id} — check compatibility."
        else:
            value = 0.6
            detail = f"License: {license_id} — verify compatibility."

        return Signal(
            name="license",
            category=SignalCategory.SECURITY,
            value=value,
            confidence=0.8,
            detail=detail,
            raw_data={"github_license": license_id, "pypi_license": pypi_license},
        )

    def _development_status(self, info: PyPIPackageInfo) -> Signal:
        """Check PyPI development status classifier."""
        status = None
        for c in info.classifiers:
            if c.startswith("Development Status ::"):
                status = c.split("::")[-1].strip()
                break

        if not status:
            return Signal(
                name="dev_status",
                category=SignalCategory.SECURITY,
                value=0.5,
                confidence=0.2,
                detail="No development status classifier on PyPI.",
            )

        status_lower = status.lower()
        if "stable" in status_lower or "mature" in status_lower:
            value = 0.9
            detail = f"Declared stable: {status}."
        elif "beta" in status_lower:
            value = 0.7
            detail = f"Beta status: {status}."
        elif "alpha" in status_lower:
            value = 0.5
            detail = f"Alpha status: {status} — expect breaking changes."
        elif "planning" in status_lower or "pre-alpha" in status_lower:
            value = 0.3
            detail = f"Early stage: {status} — not production ready."
        elif "inactive" in status_lower:
            value = 0.1
            detail = f"Declared inactive: {status}."
        else:
            value = 0.5
            detail = f"Development status: {status}."

        return Signal(
            name="dev_status",
            category=SignalCategory.SECURITY,
            value=value,
            confidence=0.5,
            detail=detail,
            raw_data={"classifier": status},
        )

    def _yanked_releases(self, info: PyPIPackageInfo) -> Signal:
        """How many releases have been yanked? High yank rate = instability."""
        if not info.releases:
            return Signal(
                name="yanked_releases",
                category=SignalCategory.SECURITY,
                value=0.5,
                confidence=0.2,
                detail="No release data.",
            )

        total = len(info.releases)
        yanked = sum(1 for r in info.releases if r.yanked)

        if total < 3:
            confidence = 0.3
        else:
            confidence = 0.6

        if yanked == 0:
            value = 0.9
            detail = f"Clean release history — 0/{total} releases yanked."
        elif yanked / total < 0.1:
            value = 0.7
            detail = f"Mostly clean — {yanked}/{total} releases yanked."
        elif yanked / total < 0.25:
            value = 0.5
            detail = f"Some instability — {yanked}/{total} releases yanked."
        else:
            value = 0.2
            detail = f"High yank rate — {yanked}/{total} releases yanked."

        return Signal(
            name="yanked_releases",
            category=SignalCategory.SECURITY,
            value=value,
            confidence=confidence,
            detail=detail,
            raw_data={"yanked": yanked, "total": total},
        )
