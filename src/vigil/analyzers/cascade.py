"""Cascade risk analysis — transitive dependency health assessment."""

from __future__ import annotations

from datetime import datetime, timezone

from vigil.clients.pypi import PyPIClient, PyPIPackageInfo
from vigil.models import DependencyNode, Signal, SignalCategory


# Depth decay weights: how much a risky dep at depth N matters
_DEPTH_WEIGHTS = {1: 1.0, 2: 0.7, 3: 0.4}


def quick_risk(info: PyPIPackageInfo) -> float:
    """Fast risk estimate from PyPI data only (no GitHub API calls).

    Returns 0.0 (safe) to 1.0 (risky).
    Uses: release recency, yank rate, release count (maturity proxy).
    """
    scores = []

    # Release recency
    dated = [r for r in info.releases if r.upload_time and not r.yanked]
    if dated:
        days_since = (datetime.now(timezone.utc) - dated[0].upload_time).days
        if days_since <= 90:
            scores.append(0.1)
        elif days_since <= 180:
            scores.append(0.2)
        elif days_since <= 365:
            scores.append(0.5)
        else:
            scores.append(0.8)
    else:
        scores.append(0.9)

    # Yank rate
    if info.releases:
        yanked = sum(1 for r in info.releases if r.yanked)
        yank_rate = yanked / len(info.releases)
        if yank_rate > 0.25:
            scores.append(0.7)
        elif yank_rate > 0.1:
            scores.append(0.4)
        else:
            scores.append(0.1)

    # Release count (maturity proxy)
    non_yanked = len([r for r in info.releases if not r.yanked])
    if non_yanked >= 20:
        scores.append(0.1)
    elif non_yanked >= 5:
        scores.append(0.2)
    elif non_yanked >= 2:
        scores.append(0.4)
    else:
        scores.append(0.7)

    return sum(scores) / len(scores) if scores else 0.5


def score_tree(tree: DependencyNode, pypi: PyPIClient) -> None:
    """Walk the tree and populate risk_score on each node using quick_risk.

    Skips the root node (depth 0) — that's the direct dep, already fully scored.
    Only scores transitive deps (depth >= 1).
    """
    for node in tree.flatten():
        if node.depth == 0:
            continue
        if node.risk_score is not None:
            continue
        info = pypi.get_package(node.package)
        if info:
            node.risk_score = quick_risk(info)
        else:
            node.risk_score = 0.9  # unknown = risky


def analyze_cascade(tree: DependencyNode, pypi: PyPIClient) -> list[Signal]:
    """Produce cascade risk signals from a resolved dependency tree.

    Returns up to 3 signals:
    - cascade_worst: the single worst transitive dependency (depth-weighted)
    - cascade_breadth: total transitive dependency count (surface area)
    - cascade_fragile: count of risky transitive dependencies
    """
    # Score all transitive nodes
    score_tree(tree, pypi)

    # Collect transitive deps (depth >= 1)
    transitive = [n for n in tree.flatten() if n.depth >= 1 and n.risk_score is not None]

    if not transitive:
        return [Signal(
            name="cascade_risk",
            category=SignalCategory.CASCADE,
            value=0.9,
            confidence=0.5,
            detail="No transitive dependencies detected.",
            raw_data={"transitive_count": 0},
        )]

    signals = []

    # 1. Worst transitive dependency (depth-weighted)
    worst_node = None
    worst_weighted = 0.0
    for node in transitive:
        weight = _DEPTH_WEIGHTS.get(node.depth, 0.3)
        weighted_risk = node.risk_score * weight
        if weighted_risk > worst_weighted:
            worst_weighted = weighted_risk
            worst_node = node

    if worst_node:
        # value = 1 - weighted_risk (invert: higher = healthier)
        value = max(0.0, min(1.0, 1.0 - worst_weighted))
        depth_label = {1: "direct dep", 2: "depth 2", 3: "depth 3"}.get(
            worst_node.depth, f"depth {worst_node.depth}"
        )
        signals.append(Signal(
            name="cascade_worst",
            category=SignalCategory.CASCADE,
            value=value,
            confidence=0.6,
            detail=(
                f"Worst transitive: {worst_node.package} ({depth_label}, "
                f"risk {worst_node.risk_score:.2f})."
            ),
            raw_data={
                "worst_package": worst_node.package,
                "worst_risk": round(worst_node.risk_score, 4),
                "worst_depth": worst_node.depth,
                "depth_weight": _DEPTH_WEIGHTS.get(worst_node.depth, 0.3),
            },
        ))

    # 2. Breadth — total transitive dependency count
    count = len(transitive)
    if count <= 5:
        breadth_value = 0.95
        breadth_detail = f"{count} transitive deps — small surface area."
    elif count <= 15:
        breadth_value = 0.75
        breadth_detail = f"{count} transitive deps — moderate surface area."
    elif count <= 30:
        breadth_value = 0.55
        breadth_detail = f"{count} transitive deps — large surface area."
    elif count <= 50:
        breadth_value = 0.35
        breadth_detail = f"{count} transitive deps — very large surface area."
    else:
        breadth_value = 0.2
        breadth_detail = f"{count} transitive deps — massive surface area."

    signals.append(Signal(
        name="cascade_breadth",
        category=SignalCategory.CASCADE,
        value=breadth_value,
        confidence=0.5,
        detail=breadth_detail,
        raw_data={"transitive_count": count},
    ))

    # 3. Fragility — how many transitive deps look risky
    fragile = [n for n in transitive if n.risk_score > 0.5]
    fragile_count = len(fragile)
    if fragile_count == 0:
        frag_value = 0.95
        frag_detail = "No fragile transitive dependencies."
    elif fragile_count <= 2:
        frag_value = 0.65
        frag_names = ", ".join(n.package for n in sorted(fragile, key=lambda n: -n.risk_score)[:2])
        frag_detail = f"{fragile_count} fragile transitive dep(s): {frag_names}."
    elif fragile_count <= 5:
        frag_value = 0.35
        frag_names = ", ".join(n.package for n in sorted(fragile, key=lambda n: -n.risk_score)[:3])
        frag_detail = f"{fragile_count} fragile transitive deps (worst: {frag_names})."
    else:
        frag_value = 0.15
        frag_detail = f"{fragile_count} fragile transitive deps — high cascade risk."

    signals.append(Signal(
        name="cascade_fragile",
        category=SignalCategory.CASCADE,
        value=frag_value,
        confidence=0.6,
        detail=frag_detail,
        raw_data={
            "fragile_count": fragile_count,
            "fragile_packages": [n.package for n in fragile],
        },
    ))

    return signals
