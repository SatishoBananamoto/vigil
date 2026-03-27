"""Sustainability analysis — org backing, funding, project age, activity ratio."""

from __future__ import annotations

from datetime import datetime, timezone

from vigil.analyzers.base import Analyzer, AnalyzerContext
from vigil.clients.github import GitHubClient, GitHubRepoInfo
from vigil.clients.pypi import PyPIPackageInfo
from vigil.models import Signal, SignalCategory


class SustainabilityAnalyzer(Analyzer):
    """Analyzes long-term sustainability signals."""

    @property
    def name(self) -> str:
        return "sustainability"

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

            # 1. Org vs personal account
            signals.append(self._org_backing(ctx.github, owner))

            # 2. Project maturity (age + activity)
            signals.append(self._project_maturity(repo_info))

            # 3. Funding signals
            signals.append(self._funding_signals(ctx.github, owner, repo))

            # 4. Issue to star ratio (proxy for maintenance load)
            signals.append(self._maintenance_load(repo_info))

        elif not repo_info:
            # No source repo found — severity depends on release recency.
            # A package with recent releases but no repo link is probably fine
            # (just old-style metadata). A package with no repo AND stale
            # releases is likely abandoned.
            recently_released = False
            if pypi_info and pypi_info.releases:
                dated = [r for r in pypi_info.releases if r.upload_time and not r.yanked]
                if dated:
                    days_since = (datetime.now(timezone.utc) - dated[0].upload_time).days
                    recently_released = days_since < 365

            if recently_released:
                # Active releases but no repo — mild concern, not a crisis
                signals.append(Signal(
                    name="no_source_repo",
                    category=SignalCategory.SUSTAINABILITY,
                    value=0.5,
                    confidence=0.4,
                    detail="No source repository linked, but has recent releases.",
                ))
            else:
                # No repo AND stale releases — strong abandonment signal
                signals.append(Signal(
                    name="no_source_repo",
                    category=SignalCategory.SUSTAINABILITY,
                    value=0.15,
                    confidence=0.7,
                    detail="No source repository linked — cannot assess maintainer health.",
                ))
                signals.append(Signal(
                    name="no_maintainer_signals",
                    category=SignalCategory.SUSTAINABILITY,
                    value=0.1,
                    confidence=0.8,
                    detail="No maintainer activity data and no recent releases — likely abandoned.",
                ))

        return signals

    def _org_backing(self, github: GitHubClient, owner: str) -> Signal:
        """Is the project backed by an organization or a solo individual?"""
        data = github._get(f"/users/{owner}")
        if not data or not isinstance(data, dict):
            return Signal(
                name="org_backing",
                category=SignalCategory.SUSTAINABILITY,
                value=0.5,
                confidence=0.3,
                detail="Could not determine owner type.",
            )

        owner_type = data.get("type", "User")
        company = data.get("company")
        public_repos = data.get("public_repos", 0)
        followers = data.get("followers", 0)

        if owner_type == "Organization":
            members = data.get("public_members_count", 0)
            if members >= 10 or public_repos >= 50:
                value = 0.9
                detail = f"Backed by organization '{owner}' ({public_repos} repos)."
            else:
                value = 0.75
                detail = f"Backed by small organization '{owner}'."
        else:
            # Individual — check for corporate affiliation
            if company:
                value = 0.65
                detail = f"Individual maintainer ({owner}) affiliated with {company}."
            elif followers >= 100:
                value = 0.55
                detail = f"Individual maintainer ({owner}) with strong following ({followers})."
            else:
                value = 0.35
                detail = f"Individual maintainer ({owner}) — sole person risk."

        return Signal(
            name="org_backing",
            category=SignalCategory.SUSTAINABILITY,
            value=value,
            confidence=0.7,
            detail=detail,
            raw_data={"owner_type": owner_type, "owner": owner, "company": company},
        )

    def _project_maturity(self, repo: GitHubRepoInfo) -> Signal:
        """Project age combined with recent activity indicates maturity."""
        if not repo.created_at:
            return Signal(
                name="project_maturity",
                category=SignalCategory.SUSTAINABILITY,
                value=0.5,
                confidence=0.2,
                detail="Unknown project age.",
            )

        now = datetime.now(timezone.utc)
        age_days = (now - repo.created_at).days
        age_years = age_days / 365.25

        # Also factor in recent push
        recently_active = False
        if repo.pushed_at:
            days_since_push = (now - repo.pushed_at).days
            recently_active = days_since_push < 90

        if age_years >= 5 and recently_active:
            value = 0.95
            detail = f"Mature and active — {age_years:.1f} years old, recently maintained."
        elif age_years >= 3 and recently_active:
            value = 0.85
            detail = f"Established and active — {age_years:.1f} years old."
        elif age_years >= 1 and recently_active:
            value = 0.7
            detail = f"Growing project — {age_years:.1f} years old, actively maintained."
        elif age_years >= 3 and not recently_active:
            value = 0.4
            detail = f"Aging without maintenance — {age_years:.1f} years old, no recent activity."
        elif age_years >= 1:
            value = 0.5
            detail = f"Project is {age_years:.1f} years old, limited recent activity."
        else:
            value = 0.45
            detail = f"Young project — {age_years:.1f} years old. Track record still forming."

        return Signal(
            name="project_maturity",
            category=SignalCategory.SUSTAINABILITY,
            value=value,
            confidence=0.6,
            detail=detail,
            raw_data={
                "age_years": round(age_years, 2),
                "recently_active": recently_active,
            },
        )

    def _funding_signals(self, github: GitHubClient, owner: str, repo: str) -> Signal:
        """Check for funding configuration (FUNDING.yml)."""
        # Check .github/FUNDING.yml via contents API
        data = github._get(f"/repos/{owner}/{repo}/contents/.github/FUNDING.yml")

        if data and isinstance(data, dict) and data.get("type") == "file":
            return Signal(
                name="funding",
                category=SignalCategory.SUSTAINABILITY,
                value=0.8,
                detail="FUNDING.yml present — project accepts sponsorship.",
                confidence=0.5,
                raw_data={"has_funding_yml": True},
            )

        # No FUNDING.yml — not necessarily bad, just no signal
        return Signal(
            name="funding",
            category=SignalCategory.SUSTAINABILITY,
            value=0.5,
            confidence=0.3,
            detail="No FUNDING.yml — unknown funding status.",
            raw_data={"has_funding_yml": False},
        )

    def _maintenance_load(self, repo: GitHubRepoInfo) -> Signal:
        """Open issues relative to stars — proxy for maintenance burden."""
        if repo.stars < 10:
            return Signal(
                name="maintenance_load",
                category=SignalCategory.SUSTAINABILITY,
                value=0.5,
                confidence=0.2,
                detail="Too few stars to assess maintenance load.",
            )

        ratio = repo.open_issues / repo.stars if repo.stars > 0 else 0

        if ratio < 0.01:
            value = 0.9
            detail = f"Low issue load — {repo.open_issues} open issues for {repo.stars:,} stars."
        elif ratio < 0.05:
            value = 0.7
            detail = f"Moderate issue load — {repo.open_issues} open issues for {repo.stars:,} stars."
        elif ratio < 0.1:
            value = 0.5
            detail = f"Heavy issue load — {repo.open_issues} open issues for {repo.stars:,} stars."
        else:
            value = 0.3
            detail = f"Overwhelming issue load — {repo.open_issues} open issues for {repo.stars:,} stars."

        return Signal(
            name="maintenance_load",
            category=SignalCategory.SUSTAINABILITY,
            value=value,
            confidence=0.4,
            detail=detail,
            raw_data={"open_issues": repo.open_issues, "stars": repo.stars, "ratio": round(ratio, 4)},
        )
