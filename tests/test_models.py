"""Tests for core data models."""

from vigil.models import (
    Dependency,
    HealthProfile,
    RiskLevel,
    ScanResult,
    Signal,
    SignalCategory,
)


def _signal(value: float, confidence: float = 1.0) -> Signal:
    return Signal(
        name="test",
        category=SignalCategory.MAINTAINER,
        value=value,
        confidence=confidence,
        detail="test signal",
    )


class TestSignal:
    def test_clamps_value(self):
        s = Signal("x", SignalCategory.MAINTAINER, 1.5, 0.5, "over")
        assert s.value == 1.0

    def test_clamps_negative(self):
        s = Signal("x", SignalCategory.MAINTAINER, -0.3, 0.5, "under")
        assert s.value == 0.0

    def test_clamps_confidence(self):
        s = Signal("x", SignalCategory.MAINTAINER, 0.5, 2.0, "over")
        assert s.confidence == 1.0


class TestDependency:
    def test_normalized_name(self):
        d = Dependency(name="My_Package.Name")
        assert d.normalized_name == "my-package-name"

    def test_simple(self):
        d = Dependency(name="requests", version_spec=">=2.28")
        assert d.name == "requests"
        assert d.version_spec == ">=2.28"


class TestHealthProfile:
    def test_no_signals_is_unknown(self):
        p = HealthProfile(package="test")
        assert p.risk_level == RiskLevel.UNKNOWN
        assert p.risk_score == 1.0

    def test_perfect_health(self):
        p = HealthProfile(package="test", signals=[_signal(1.0)])
        assert p.risk_score == 0.0
        assert p.risk_level == RiskLevel.LOW

    def test_critical_health(self):
        p = HealthProfile(package="test", signals=[_signal(0.1)])
        assert p.risk_score == 0.9
        assert p.risk_level == RiskLevel.CRITICAL

    def test_moderate_health(self):
        p = HealthProfile(package="test", signals=[_signal(0.6)])
        assert p.risk_score == 0.4
        assert p.risk_level == RiskLevel.MODERATE

    def test_confidence_weighting(self):
        # High-confidence bad signal + low-confidence good signal
        p = HealthProfile(
            package="test",
            signals=[_signal(0.1, confidence=1.0), _signal(0.9, confidence=0.1)],
        )
        # Should lean toward the bad signal
        assert p.risk_score > 0.7

    def test_worst_signals(self):
        p = HealthProfile(
            package="test",
            signals=[_signal(0.8), _signal(0.2), _signal(0.5)],
        )
        worst = p.worst_signals
        assert worst[0].value == 0.2
        assert worst[-1].value == 0.8

    def test_signals_by_category(self):
        p = HealthProfile(
            package="test",
            signals=[
                Signal("a", SignalCategory.MAINTAINER, 0.5, 1.0, ""),
                Signal("b", SignalCategory.COMMUNITY, 0.5, 1.0, ""),
                Signal("c", SignalCategory.MAINTAINER, 0.3, 1.0, ""),
            ],
        )
        assert len(p.signals_by_category(SignalCategory.MAINTAINER)) == 2
        assert len(p.signals_by_category(SignalCategory.COMMUNITY)) == 1
        assert len(p.signals_by_category(SignalCategory.SECURITY)) == 0


class TestScanResult:
    def test_counts(self):
        r = ScanResult(dependencies=[])
        r.profiles["a"] = HealthProfile(package="a", signals=[_signal(0.05)])
        r.profiles["b"] = HealthProfile(package="b", signals=[_signal(0.8)])
        r.profiles["c"] = HealthProfile(package="c")  # unknown

        assert r.critical_count == 1
        assert r.high_count == 0
        assert r.unknown_count == 1
