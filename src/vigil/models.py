"""Core data models for vigil."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class RiskLevel(Enum):
    """Discrete risk classification."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SignalCategory(Enum):
    """Dimensions of dependency health."""

    MAINTAINER = "maintainer"
    COMMUNITY = "community"
    SECURITY = "security"
    SUSTAINABILITY = "sustainability"
    REGULATORY = "regulatory"
    CASCADE = "cascade"


@dataclass
class Signal:
    """A single health measurement from an analyzer.

    Values are normalized 0-1 where 1 = healthiest, 0 = worst.
    Confidence indicates how much we trust this measurement.
    """

    name: str
    category: SignalCategory
    value: float  # 0 (worst) to 1 (best)
    confidence: float  # 0 (no data) to 1 (certain)
    detail: str  # human-readable explanation
    raw_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.value = max(0.0, min(1.0, self.value))
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class Dependency:
    """A parsed dependency from a requirements file."""

    name: str
    version_spec: str | None = None
    extras: list[str] = field(default_factory=list)

    @property
    def normalized_name(self) -> str:
        """PEP 503 normalized name."""
        return self.name.lower().replace("-", "-").replace("_", "-").replace(".", "-")


@dataclass
class DependencyNode:
    """A node in the transitive dependency tree."""

    package: str
    version: str | None = None
    depth: int = 0
    children: list[DependencyNode] = field(default_factory=list)
    risk_score: float | None = None  # PyPI-only quick risk estimate

    @property
    def total_nodes(self) -> int:
        """Total nodes in this subtree (including self)."""
        return 1 + sum(c.total_nodes for c in self.children)

    def flatten(self) -> list[DependencyNode]:
        """All nodes in the tree as a flat list (BFS order)."""
        result = []
        queue = [self]
        while queue:
            node = queue.pop(0)
            result.append(node)
            queue.extend(node.children)
        return result


@dataclass
class HealthProfile:
    """Multi-dimensional health assessment for a single dependency."""

    package: str
    version: str | None = None
    repo_url: str | None = None
    signals: list[Signal] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None  # if assessment failed
    dependency_tree: DependencyNode | None = None

    @property
    def risk_score(self) -> float:
        """Aggregate risk score: 0 = safest, 1 = riskiest.

        Weighted by confidence — low-confidence signals pull less.
        No signals = maximum risk (unknown is dangerous).
        """
        if not self.signals:
            return 1.0
        total_weight = sum(s.confidence for s in self.signals)
        if total_weight == 0:
            return 1.0
        weighted_health = sum(s.value * s.confidence for s in self.signals)
        return 1.0 - (weighted_health / total_weight)

    @property
    def risk_level(self) -> RiskLevel:
        if not self.signals:
            return RiskLevel.UNKNOWN
        score = self.risk_score
        if score < 0.25:
            return RiskLevel.LOW
        if score < 0.50:
            return RiskLevel.MODERATE
        if score < 0.75:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def signals_by_category(self, category: SignalCategory) -> list[Signal]:
        return [s for s in self.signals if s.category == category]

    @property
    def worst_signals(self) -> list[Signal]:
        """Signals sorted by severity (lowest value first)."""
        return sorted(self.signals, key=lambda s: s.value)


@dataclass
class ScanResult:
    """Complete scan output for all dependencies."""

    dependencies: list[Dependency]
    profiles: dict[str, HealthProfile] = field(default_factory=dict)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_file: str | None = None

    @property
    def critical_count(self) -> int:
        return sum(1 for p in self.profiles.values() if p.risk_level == RiskLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for p in self.profiles.values() if p.risk_level == RiskLevel.HIGH)

    @property
    def unknown_count(self) -> int:
        return sum(1 for p in self.profiles.values() if p.risk_level == RiskLevel.UNKNOWN)
