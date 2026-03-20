"""Community health analysis — issue velocity, contributor diversity, responsiveness."""

from __future__ import annotations

from datetime import datetime, timezone

from vigil.analyzers.base import Analyzer, AnalyzerContext
from vigil.clients.github import GitHubRepoInfo
from vigil.clients.pypi import PyPIPackageInfo
from vigil.models import Signal, SignalCategory


class CommunityAnalyzer(Analyzer):
    """Analyzes community health signals around a project."""

    @property
    def name(self) -> str:
        return "community"

    def analyze(
        self,
        package: str,
        ctx: AnalyzerContext,
        pypi_info: PyPIPackageInfo | None = None,
        repo_info: GitHubRepoInfo | None = None,
    ) -> list[Signal]:
        if not repo_info or repo_info.archived:
            return []

        signals = []
        owner, repo = repo_info.owner, repo_info.name

        # 1. Issue response time
        issues = ctx.github.get_recent_issues(owner, repo, state="all", limit=30)
        if issues:
            signals.append(self._issue_responsiveness(issues))
            signals.append(self._issue_close_rate(issues))

        # 2. Contributor diversity (beyond bus factor — growth signal)
        contributors = ctx.github.get_contributors(owner, repo)
        if contributors:
            signals.append(self._contributor_breadth(contributors))

        # 3. Star momentum (proxy for community interest)
        signals.append(self._community_size(repo_info))

        return signals

    def _issue_responsiveness(self, issues: list[dict]) -> Signal:
        """How quickly do issues get a first response?

        We approximate by looking at the gap between created_at and updated_at
        for recently created issues. Not perfect (update could be bot/label),
        but a reasonable proxy without paginating comments.
        """
        response_times = []
        for issue in issues:
            # Skip PRs
            if "pull_request" in issue:
                continue
            created = _parse_dt(issue.get("created_at"))
            updated = _parse_dt(issue.get("updated_at"))
            if not created or not updated:
                continue
            if created == updated:
                continue  # never updated
            delta_hours = (updated - created).total_seconds() / 3600
            if delta_hours > 0:
                response_times.append(delta_hours)

        if len(response_times) < 3:
            return Signal(
                name="issue_responsiveness",
                category=SignalCategory.COMMUNITY,
                value=0.5,
                confidence=0.2,
                detail="Insufficient issue data for response time analysis.",
            )

        median_hours = sorted(response_times)[len(response_times) // 2]

        if median_hours <= 24:
            value = 0.95
            detail = f"Fast — median first activity within {median_hours:.0f}h."
        elif median_hours <= 72:
            value = 0.8
            detail = f"Good — median first activity within {median_hours:.0f}h."
        elif median_hours <= 168:  # 1 week
            value = 0.6
            detail = f"Moderate — median first activity within {median_hours:.0f}h."
        elif median_hours <= 720:  # 30 days
            value = 0.35
            detail = f"Slow — median first activity within {median_hours:.0f}h."
        else:
            value = 0.15
            detail = f"Very slow — median first activity within {median_hours:.0f}h."

        return Signal(
            name="issue_responsiveness",
            category=SignalCategory.COMMUNITY,
            value=value,
            confidence=0.5,  # proxy metric, not exact
            detail=detail,
            raw_data={
                "median_hours": round(median_hours, 1),
                "sample_size": len(response_times),
            },
        )

    def _issue_close_rate(self, issues: list[dict]) -> Signal:
        """What fraction of recent issues are closed?"""
        # Filter to actual issues (not PRs)
        real_issues = [i for i in issues if "pull_request" not in i]
        if len(real_issues) < 3:
            return Signal(
                name="issue_close_rate",
                category=SignalCategory.COMMUNITY,
                value=0.5,
                confidence=0.2,
                detail="Insufficient issue data.",
            )

        closed = sum(1 for i in real_issues if i.get("state") == "closed")
        rate = closed / len(real_issues)

        if rate >= 0.8:
            value, detail = 0.9, f"High close rate — {rate:.0%} of recent issues resolved."
        elif rate >= 0.6:
            value, detail = 0.7, f"Moderate close rate — {rate:.0%} of recent issues resolved."
        elif rate >= 0.4:
            value, detail = 0.5, f"Low close rate — {rate:.0%} of recent issues resolved."
        else:
            value, detail = 0.2, f"Very low close rate — {rate:.0%} of recent issues resolved."

        return Signal(
            name="issue_close_rate",
            category=SignalCategory.COMMUNITY,
            value=value,
            confidence=0.5,
            detail=detail,
            raw_data={"closed": closed, "total": len(real_issues), "rate": round(rate, 3)},
        )

    def _contributor_breadth(self, contributors: list) -> Signal:
        """How many active contributors does the project have?"""
        count = len(contributors)

        if count >= 30:
            value = 0.95
            detail = f"Broad contributor base — {count}+ contributors."
        elif count >= 15:
            value = 0.8
            detail = f"Healthy contributor count — {count} contributors."
        elif count >= 5:
            value = 0.6
            detail = f"Small team — {count} contributors."
        elif count >= 2:
            value = 0.35
            detail = f"Very small team — {count} contributors."
        else:
            value = 0.15
            detail = f"Solo project — {count} contributor."

        return Signal(
            name="contributor_breadth",
            category=SignalCategory.COMMUNITY,
            value=value,
            confidence=0.7,
            detail=detail,
            raw_data={"contributor_count": count},
        )

    def _community_size(self, repo: GitHubRepoInfo) -> Signal:
        """Stars as a proxy for community interest and visibility."""
        stars = repo.stars

        if stars >= 10000:
            value = 0.95
            detail = f"High visibility — {stars:,} stars."
        elif stars >= 1000:
            value = 0.8
            detail = f"Well-known — {stars:,} stars."
        elif stars >= 100:
            value = 0.6
            detail = f"Moderate visibility — {stars:,} stars."
        elif stars >= 10:
            value = 0.4
            detail = f"Low visibility — {stars:,} stars."
        else:
            value = 0.2
            detail = f"Very low visibility — {stars:,} stars."

        return Signal(
            name="community_size",
            category=SignalCategory.COMMUNITY,
            value=value,
            confidence=0.4,  # stars are a weak signal
            detail=detail,
            raw_data={"stars": stars, "forks": repo.forks},
        )


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
