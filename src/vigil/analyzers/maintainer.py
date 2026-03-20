"""Maintainer activity and bus factor analysis."""

from __future__ import annotations

from datetime import datetime, timezone

from vigil.analyzers.base import Analyzer, AnalyzerContext
from vigil.clients.github import GitHubRepoInfo
from vigil.clients.pypi import PyPIPackageInfo
from vigil.models import Signal, SignalCategory


class MaintainerAnalyzer(Analyzer):
    """Analyzes maintainer activity patterns and bus factor."""

    @property
    def name(self) -> str:
        return "maintainer"

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

            # 1. Recent push activity
            signals.append(self._push_recency(repo_info))

            # 2. Commit activity trend
            activity = ctx.github.get_commit_activity(owner, repo)
            if activity:
                signals.append(self._commit_trend(activity.weeks))

            # 3. Bus factor (contributor concentration)
            contributors = ctx.github.get_contributors(owner, repo)
            if contributors:
                signals.append(self._bus_factor(contributors))

        elif repo_info and repo_info.archived:
            signals.append(Signal(
                name="repo_archived",
                category=SignalCategory.MAINTAINER,
                value=0.0,
                confidence=1.0,
                detail=f"Repository {repo_info.full_name} is archived — no longer maintained.",
            ))

        # Release cadence from PyPI
        if pypi_info and pypi_info.releases:
            signals.append(self._release_cadence(pypi_info))

        return signals

    def _push_recency(self, repo: GitHubRepoInfo) -> Signal:
        """How recently was the repo pushed to?"""
        if not repo.pushed_at:
            return Signal(
                name="push_recency",
                category=SignalCategory.MAINTAINER,
                value=0.3,
                confidence=0.3,
                detail="No push timestamp available.",
            )

        now = datetime.now(timezone.utc)
        days_since = (now - repo.pushed_at).days

        if days_since <= 7:
            value, detail = 1.0, f"Active — last push {days_since}d ago."
        elif days_since <= 30:
            value, detail = 0.9, f"Recent activity — last push {days_since}d ago."
        elif days_since <= 90:
            value, detail = 0.7, f"Moderate activity — last push {days_since}d ago."
        elif days_since <= 180:
            value, detail = 0.5, f"Slowing — last push {days_since}d ago."
        elif days_since <= 365:
            value, detail = 0.3, f"Stale — last push {days_since}d ago."
        else:
            value, detail = 0.1, f"Inactive — last push {days_since}d ago."

        return Signal(
            name="push_recency",
            category=SignalCategory.MAINTAINER,
            value=value,
            confidence=0.8,
            detail=detail,
            raw_data={"days_since_push": days_since},
        )

    def _commit_trend(self, weeks: list[dict]) -> Signal:
        """Is commit activity trending up, stable, or declining?"""
        if len(weeks) < 12:
            return Signal(
                name="commit_trend",
                category=SignalCategory.MAINTAINER,
                value=0.5,
                confidence=0.2,
                detail="Insufficient history for trend analysis.",
            )

        # Compare last quarter vs previous quarter
        recent = weeks[-13:]  # last ~3 months
        previous = weeks[-26:-13]  # 3-6 months ago

        recent_total = sum(w.get("total", 0) for w in recent)
        previous_total = sum(w.get("total", 0) for w in previous)

        if previous_total == 0 and recent_total == 0:
            return Signal(
                name="commit_trend",
                category=SignalCategory.MAINTAINER,
                value=0.1,
                confidence=0.7,
                detail="No commits in last 6 months.",
                raw_data={"recent": recent_total, "previous": previous_total},
            )

        if previous_total == 0:
            ratio = 2.0  # came back from dead
        else:
            ratio = recent_total / previous_total

        if ratio >= 1.2:
            value, detail = 0.9, f"Growing — commits up {ratio:.0%} quarter-over-quarter."
        elif ratio >= 0.8:
            value, detail = 0.7, f"Stable — commits at {ratio:.0%} of previous quarter."
        elif ratio >= 0.4:
            value, detail = 0.4, f"Declining — commits at {ratio:.0%} of previous quarter."
        else:
            value, detail = 0.15, f"Dropping fast — commits at {ratio:.0%} of previous quarter."

        return Signal(
            name="commit_trend",
            category=SignalCategory.MAINTAINER,
            value=value,
            confidence=0.7,
            detail=detail,
            raw_data={"recent": recent_total, "previous": previous_total, "ratio": round(ratio, 3)},
        )

    def _bus_factor(self, contributors: list) -> Signal:
        """How concentrated is commit activity among contributors?"""
        if not contributors:
            return Signal(
                name="bus_factor",
                category=SignalCategory.MAINTAINER,
                value=0.2,
                confidence=0.5,
                detail="No contributor data available.",
            )

        total = sum(c.contributions for c in contributors)
        if total == 0:
            return Signal(
                name="bus_factor",
                category=SignalCategory.MAINTAINER,
                value=0.2,
                confidence=0.3,
                detail="No contributions recorded.",
            )

        # Count how many people own 80% of commits
        sorted_contribs = sorted(contributors, key=lambda c: c.contributions, reverse=True)
        cumulative = 0
        bus_factor = 0
        for c in sorted_contribs:
            cumulative += c.contributions
            bus_factor += 1
            if cumulative >= total * 0.8:
                break

        if bus_factor == 1:
            value = 0.1
            detail = f"Bus factor 1 — single maintainer owns 80%+ of commits ({sorted_contribs[0].login})."
        elif bus_factor == 2:
            value = 0.3
            detail = f"Bus factor 2 — two people own 80%+ of commits."
        elif bus_factor <= 4:
            value = 0.6
            detail = f"Bus factor {bus_factor} — small core team."
        elif bus_factor <= 10:
            value = 0.8
            detail = f"Bus factor {bus_factor} — healthy contributor base."
        else:
            value = 0.95
            detail = f"Bus factor {bus_factor} — broad contributor base."

        return Signal(
            name="bus_factor",
            category=SignalCategory.MAINTAINER,
            value=value,
            confidence=0.8,
            detail=detail,
            raw_data={
                "bus_factor": bus_factor,
                "total_contributors": len(contributors),
                "top_contributor": sorted_contribs[0].login if sorted_contribs else None,
                "top_contributor_pct": round(sorted_contribs[0].contributions / total, 3) if sorted_contribs else 0,
            },
        )

    def _release_cadence(self, info: PyPIPackageInfo) -> Signal:
        """How frequently are releases published?"""
        dated = [r for r in info.releases if r.upload_time and not r.yanked]
        if len(dated) < 2:
            return Signal(
                name="release_cadence",
                category=SignalCategory.MAINTAINER,
                value=0.3,
                confidence=0.3,
                detail="Insufficient release history.",
            )

        # Time between last two releases
        latest = dated[0].upload_time
        previous = dated[1].upload_time
        days_between = (latest - previous).days

        # Time since last release
        now = datetime.now(timezone.utc)
        days_since_latest = (now - latest).days

        # Recent release + reasonable cadence = healthy
        if days_since_latest <= 90 and days_between <= 180:
            value = 0.9
            detail = f"Active releases — latest {days_since_latest}d ago, {days_between}d between last two."
        elif days_since_latest <= 180:
            value = 0.7
            detail = f"Moderate release pace — latest {days_since_latest}d ago."
        elif days_since_latest <= 365:
            value = 0.4
            detail = f"Slow releases — latest {days_since_latest}d ago."
        else:
            value = 0.15
            detail = f"Stale — last release {days_since_latest}d ago."

        return Signal(
            name="release_cadence",
            category=SignalCategory.MAINTAINER,
            value=value,
            confidence=0.6,
            detail=detail,
            raw_data={
                "days_since_latest": days_since_latest,
                "days_between_last_two": days_between,
                "total_releases": len(dated),
            },
        )
