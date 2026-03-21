"""Tests for cascade risk analysis."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from vigil.analyzers.cascade import analyze_cascade, quick_risk
from vigil.clients.pypi import PyPIPackageInfo, PyPIRelease
from vigil.models import DependencyNode, SignalCategory


def _pypi_info(
    name: str = "test",
    days_since_release: int = 30,
    total_releases: int = 10,
    yanked_count: int = 0,
) -> PyPIPackageInfo:
    """Create a PyPIPackageInfo with controllable parameters."""
    now = datetime.now(timezone.utc)
    releases = []
    for i in range(total_releases):
        releases.append(PyPIRelease(
            version=f"{total_releases - i}.0.0",
            upload_time=now - timedelta(days=days_since_release + i * 30),
            yanked=(i < yanked_count),
        ))
    return PyPIPackageInfo(name=name, version="1.0.0", releases=releases)


def _mock_pypi(packages: dict[str, PyPIPackageInfo]) -> MagicMock:
    client = MagicMock()
    client.get_package = lambda name: packages.get(name)
    return client


class TestQuickRisk:
    def test_healthy_package(self):
        info = _pypi_info(days_since_release=10, total_releases=25, yanked_count=0)
        risk = quick_risk(info)
        assert risk < 0.2  # low risk

    def test_stale_package(self):
        info = _pypi_info(days_since_release=400, total_releases=5, yanked_count=0)
        risk = quick_risk(info)
        assert risk > 0.3  # elevated risk (stale release + moderate maturity)

    def test_high_yank_rate(self):
        info = _pypi_info(days_since_release=30, total_releases=10, yanked_count=4)
        risk = quick_risk(info)
        assert risk > 0.3  # yanks increase risk

    def test_very_few_releases(self):
        info = _pypi_info(days_since_release=30, total_releases=1, yanked_count=0)
        risk = quick_risk(info)
        assert risk > 0.2  # low maturity

    def test_no_releases(self):
        info = PyPIPackageInfo(name="empty", version="0.0.1", releases=[])
        risk = quick_risk(info)
        assert risk > 0.7  # very risky


class TestAnalyzeCascade:
    def test_no_transitive_deps(self):
        tree = DependencyNode(package="solo", depth=0, children=[])
        pypi = _mock_pypi({})
        signals = analyze_cascade(tree, pypi)

        assert len(signals) == 1
        assert signals[0].name == "cascade_risk"
        assert signals[0].value == 0.9  # no deps = low cascade risk

    def test_healthy_tree(self):
        healthy_info = _pypi_info("child", days_since_release=10, total_releases=30)
        tree = DependencyNode(
            package="root", depth=0,
            children=[
                DependencyNode(package="child-a", depth=1),
                DependencyNode(package="child-b", depth=1),
            ],
        )
        pypi = _mock_pypi({"child-a": healthy_info, "child-b": healthy_info})
        signals = analyze_cascade(tree, pypi)

        # Should produce 3 signals
        assert len(signals) == 3
        names = {s.name for s in signals}
        assert names == {"cascade_worst", "cascade_breadth", "cascade_fragile"}

        # All should be healthy
        for s in signals:
            assert s.category == SignalCategory.CASCADE
            assert s.value >= 0.6

    def test_risky_transitive_dep(self):
        # Use very stale + very few releases to push risk above 0.5
        stale_info = _pypi_info("stale-dep", days_since_release=500, total_releases=1)
        healthy_info = _pypi_info("healthy-dep", days_since_release=10, total_releases=30)
        tree = DependencyNode(
            package="root", depth=0,
            children=[
                DependencyNode(package="stale-dep", depth=1),
                DependencyNode(package="healthy-dep", depth=1),
            ],
        )
        pypi = _mock_pypi({"stale-dep": stale_info, "healthy-dep": healthy_info})
        signals = analyze_cascade(tree, pypi)

        worst = next(s for s in signals if s.name == "cascade_worst")
        assert "stale-dep" in worst.detail
        assert worst.value < 0.5  # risky transitive dep pulls value down

        fragile = next(s for s in signals if s.name == "cascade_fragile")
        assert fragile.raw_data["fragile_count"] >= 1

    def test_depth_weighting(self):
        """Risk at depth 2 should matter less than risk at depth 1."""
        stale_info = _pypi_info("deep-stale", days_since_release=500, total_releases=2)
        tree_shallow = DependencyNode(
            package="root", depth=0,
            children=[DependencyNode(package="deep-stale", depth=1)],
        )
        tree_deep = DependencyNode(
            package="root", depth=0,
            children=[
                DependencyNode(
                    package="mid", depth=1,
                    children=[DependencyNode(package="deep-stale", depth=2)],
                ),
            ],
        )
        pypi = _mock_pypi({
            "deep-stale": stale_info,
            "mid": _pypi_info("mid", days_since_release=10, total_releases=20),
        })

        signals_shallow = analyze_cascade(tree_shallow, pypi)
        signals_deep = analyze_cascade(tree_deep, pypi)

        worst_shallow = next(s for s in signals_shallow if s.name == "cascade_worst")
        worst_deep = next(s for s in signals_deep if s.name == "cascade_worst")

        # Same risky dep at depth 1 should produce lower value (worse) than at depth 2
        assert worst_shallow.value < worst_deep.value

    def test_breadth_scoring(self):
        info = _pypi_info("dep", days_since_release=30, total_releases=10)
        children = [DependencyNode(package=f"dep-{i}", depth=1) for i in range(20)]
        tree = DependencyNode(package="root", depth=0, children=children)
        pypi = _mock_pypi({f"dep-{i}": info for i in range(20)})

        signals = analyze_cascade(tree, pypi)
        breadth = next(s for s in signals if s.name == "cascade_breadth")
        assert breadth.value < 0.7  # 20 deps = large surface area

    def test_unknown_transitive_is_risky(self):
        tree = DependencyNode(
            package="root", depth=0,
            children=[DependencyNode(package="mystery-pkg", depth=1)],
        )
        pypi = _mock_pypi({})  # mystery-pkg not on PyPI

        signals = analyze_cascade(tree, pypi)
        worst = next(s for s in signals if s.name == "cascade_worst")
        # Unknown dep should get high risk score (0.9)
        assert worst.value < 0.3

    def test_signal_categories(self):
        info = _pypi_info("dep", days_since_release=30, total_releases=10)
        tree = DependencyNode(
            package="root", depth=0,
            children=[DependencyNode(package="dep", depth=1)],
        )
        pypi = _mock_pypi({"dep": info})
        signals = analyze_cascade(tree, pypi)

        for s in signals:
            assert s.category == SignalCategory.CASCADE
