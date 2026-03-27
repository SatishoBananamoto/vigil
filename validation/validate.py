"""Retroactive validation: do vigil's signals distinguish healthy from abandoned packages?

Runs vigil against a curated test set and compares actual risk scores
to expected risk levels. Outputs a report showing hits, misses, and
threshold effectiveness.

Usage:
    python validation/validate.py [--cascade]

Requires GITHUB_TOKEN for meaningful results (vigil auth login).
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add src to path so we can import vigil directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vigil.analyzers.base import AnalyzerContext
from vigil.analyzers.community import CommunityAnalyzer
from vigil.analyzers.maintainer import MaintainerAnalyzer
from vigil.analyzers.security import SecurityAnalyzer
from vigil.analyzers.sustainability import SustainabilityAnalyzer
from vigil.analyzers.cascade import analyze_cascade
from vigil.clients.github import GitHubClient, RateLimitError, parse_github_url
from vigil.clients.pypi import PyPIClient
from vigil.models import HealthProfile, RiskLevel
from vigil.resolver import DependencyResolver


# --- Test set ---
# Each entry: (package_name, expected_risk_level, reason)

EXPECTED_HEALTHY = [
    ("requests", RiskLevel.LOW, "Most popular HTTP library, well-maintained"),
    ("flask", RiskLevel.LOW, "Major web framework, Pallets team"),
    ("django", RiskLevel.LOW, "Largest Python web framework, strong community"),
    ("pytest", RiskLevel.LOW, "Standard test framework, very active"),
    ("click", RiskLevel.LOW, "CLI framework, Pallets team"),
    ("httpx", RiskLevel.LOW, "Modern HTTP client, actively maintained"),
    ("rich", RiskLevel.LOW, "Terminal rendering, Will McGugan, very active"),
    ("fastapi", RiskLevel.LOW, "Modern web framework, rapid growth"),
    ("pydantic", RiskLevel.LOW, "Data validation, core to FastAPI ecosystem"),
    ("numpy", RiskLevel.LOW, "Scientific computing foundation, NumFOCUS backed"),
]

EXPECTED_RISKY = [
    ("pycrypto", RiskLevel.CRITICAL, "Abandoned since 2014, known CVEs, 1.5M downloads/month"),
    ("nose", RiskLevel.CRITICAL, "Abandoned since 2015, broken on Python 3.12"),
    ("distribute", RiskLevel.HIGH, "Superseded by setuptools, abandoned"),
    ("mimeparse", RiskLevel.HIGH, "Unmaintained, last release 2014"),
    ("pep8", RiskLevel.HIGH, "Renamed to pycodestyle, original abandoned"),
]

EXPECTED_MODERATE = [
    ("setuptools", RiskLevel.MODERATE, "Had maintenance scare 2025, recovered"),
    ("colorama", RiskLevel.MODERATE, "No PyPI release in 3+ years, 133 open issues, no repo link in metadata"),
    ("deep-translator", RiskLevel.MODERATE, "Was hijacked, legitimate version restored"),
    ("ultralytics", RiskLevel.LOW, "CI/CD compromised Dec 2024, but very active project"),
    ("pillow", RiskLevel.LOW, "Fork of abandoned PIL, actively maintained"),
]

ANALYZERS = [
    MaintainerAnalyzer(),
    CommunityAnalyzer(),
    SecurityAnalyzer(),
    SustainabilityAnalyzer(),
]


@dataclass
class ValidationResult:
    package: str
    expected_level: RiskLevel
    actual_level: RiskLevel
    actual_score: float
    reason: str
    signals_fired: list[dict]
    match: bool
    error: str | None = None


def analyze_package(
    name: str, ctx: AnalyzerContext, resolver: DependencyResolver | None = None
) -> HealthProfile:
    """Run all analyzers against a package."""
    profile = HealthProfile(package=name)

    pypi_info = ctx.pypi.get_package(name)
    if not pypi_info:
        profile.error = f"Not found on PyPI"
        return profile

    profile.version = pypi_info.version
    profile.repo_url = pypi_info.repo_url

    repo_info = None
    if pypi_info.repo_url:
        parsed = parse_github_url(pypi_info.repo_url)
        if parsed:
            owner, repo = parsed
            repo_info = ctx.github.get_repo(owner, repo)

    for analyzer in ANALYZERS:
        try:
            signals = analyzer.analyze(name, ctx, pypi_info=pypi_info, repo_info=repo_info)
            profile.signals.extend(signals)
        except RateLimitError:
            raise
        except Exception as e:
            print(f"  {analyzer.name} failed for {name}: {e}")

    if resolver:
        try:
            tree = resolver.resolve(name)
            profile.dependency_tree = tree
            cascade_signals = analyze_cascade(tree, ctx.pypi)
            profile.signals.extend(cascade_signals)
        except Exception as e:
            print(f"  cascade failed for {name}: {e}")

    return profile


def level_distance(expected: RiskLevel, actual: RiskLevel) -> int:
    """How far apart are two risk levels? 0 = exact match."""
    order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.UNKNOWN]
    try:
        return abs(order.index(expected) - order.index(actual))
    except ValueError:
        return 99


def run_validation(use_cascade: bool = False) -> list[ValidationResult]:
    """Run vigil against the full test set and collect results."""
    all_packages = (
        [(p, e, r) for p, e, r in EXPECTED_HEALTHY]
        + [(p, e, r) for p, e, r in EXPECTED_RISKY]
        + [(p, e, r) for p, e, r in EXPECTED_MODERATE]
    )

    results = []

    with PyPIClient() as pypi, GitHubClient() as github:
        # Check auth status
        if not github.authenticated:
            print("WARNING: Not authenticated. Will hit rate limit after ~8 packages.")
            print("Run: vigil auth login")
            print()

        try:
            status = github.rate_limit_status()
            remaining = status["remaining"]
            needed = len(all_packages) * 7
            print(f"Budget: {remaining} requests, ~{needed} needed for {len(all_packages)} packages")
            if remaining < needed:
                print(f"WARNING: May not complete all packages. Will scan until budget runs out.")
            print()
        except Exception:
            pass

        ctx = AnalyzerContext(github=github, pypi=pypi)
        resolver = DependencyResolver(pypi) if use_cascade else None

        for name, expected, reason in all_packages:
            print(f"Scanning {name}...", end=" ", flush=True)
            try:
                profile = analyze_package(name, ctx, resolver)
                actual_level = profile.risk_level
                actual_score = profile.risk_score

                # Allow one level of tolerance for "match"
                match = level_distance(expected, actual_level) <= 1

                signals_fired = [
                    {
                        "name": s.name,
                        "category": s.category.value,
                        "value": round(s.value, 3),
                        "confidence": round(s.confidence, 3),
                        "detail": s.detail,
                    }
                    for s in profile.signals
                ]

                result = ValidationResult(
                    package=name,
                    expected_level=expected,
                    actual_level=actual_level,
                    actual_score=round(actual_score, 4),
                    reason=reason,
                    signals_fired=signals_fired,
                    match=match,
                    error=profile.error,
                )
                print(f"{actual_level.value.upper()} (score: {actual_score:.3f}) {'OK' if match else 'MISS'}")

            except RateLimitError as e:
                print(f"RATE LIMIT HIT — stopping")
                result = ValidationResult(
                    package=name,
                    expected_level=expected,
                    actual_level=RiskLevel.UNKNOWN,
                    actual_score=1.0,
                    reason=reason,
                    signals_fired=[],
                    match=False,
                    error=str(e),
                )
                results.append(result)
                break

            except Exception as e:
                print(f"ERROR: {e}")
                result = ValidationResult(
                    package=name,
                    expected_level=expected,
                    actual_level=RiskLevel.UNKNOWN,
                    actual_score=1.0,
                    reason=reason,
                    signals_fired=[],
                    match=False,
                    error=str(e),
                )

            results.append(result)

    return results


def print_report(results: list[ValidationResult]) -> None:
    """Print a summary report of validation results."""
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)

    hits = sum(1 for r in results if r.match and not r.error)
    misses = [r for r in results if not r.match and not r.error]
    errors = [r for r in results if r.error]
    total_scored = len(results) - len(errors)

    print(f"\nPackages tested: {len(results)}")
    print(f"Matches (within 1 level): {hits}/{total_scored} ({hits/total_scored*100:.0f}%)" if total_scored else "No packages scored")
    print(f"Misses: {len(misses)}")
    print(f"Errors: {len(errors)}")

    if misses:
        print(f"\n--- MISSES ---")
        for r in misses:
            print(f"  {r.package}: expected {r.expected_level.value}, got {r.actual_level.value} (score: {r.actual_score})")
            print(f"    Reason: {r.reason}")
            # Show worst signals
            worst = sorted(r.signals_fired, key=lambda s: s["value"])[:3]
            for s in worst:
                print(f"    -> {s['name']}: {s['value']} — {s['detail']}")

    if errors:
        print(f"\n--- ERRORS ---")
        for r in errors:
            print(f"  {r.package}: {r.error}")

    # Category breakdown
    print(f"\n--- CATEGORY BREAKDOWN ---")
    for category, packages in [
        ("Healthy (expected LOW)", [r for r in results if r.expected_level == RiskLevel.LOW and not r.error]),
        ("Risky (expected HIGH/CRITICAL)", [r for r in results if r.expected_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not r.error]),
        ("Moderate (expected MODERATE)", [r for r in results if r.expected_level == RiskLevel.MODERATE and not r.error]),
    ]:
        if not packages:
            continue
        avg_score = sum(r.actual_score for r in packages) / len(packages)
        matches = sum(1 for r in packages if r.match)
        print(f"  {category}: avg score {avg_score:.3f}, {matches}/{len(packages)} match")
        for r in packages:
            icon = "OK" if r.match else "MISS"
            print(f"    {icon} {r.package}: {r.actual_level.value} ({r.actual_score:.3f})")


def save_results(results: list[ValidationResult], path: Path) -> None:
    """Save raw results as JSON for later analysis."""
    data = []
    for r in results:
        data.append({
            "package": r.package,
            "expected_level": r.expected_level.value,
            "actual_level": r.actual_level.value,
            "actual_score": r.actual_score,
            "match": r.match,
            "reason": r.reason,
            "error": r.error,
            "signals": r.signals_fired,
        })
    path.write_text(json.dumps(data, indent=2))
    print(f"\nRaw results saved to {path}")


if __name__ == "__main__":
    use_cascade = "--cascade" in sys.argv

    print("vigil threshold validation")
    print(f"Cascade: {'enabled' if use_cascade else 'disabled'}")
    print(f"Test set: {len(EXPECTED_HEALTHY)} healthy + {len(EXPECTED_RISKY)} risky + {len(EXPECTED_MODERATE)} moderate")
    print()

    results = run_validation(use_cascade)
    print_report(results)

    out_path = Path(__file__).parent / "results.json"
    save_results(results, out_path)
