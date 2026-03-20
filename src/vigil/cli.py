"""CLI entry point for vigil."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from vigil import __version__
from vigil.analyzers.base import AnalyzerContext
from vigil.analyzers.community import CommunityAnalyzer
from vigil.analyzers.maintainer import MaintainerAnalyzer
from vigil.analyzers.security import SecurityAnalyzer
from vigil.analyzers.sustainability import SustainabilityAnalyzer
from vigil.clients.github import GitHubClient, parse_github_url
from vigil.clients.pypi import PyPIClient
from vigil.models import HealthProfile, ScanResult
from vigil.output import render_detail, render_scan
from vigil.parsers import parse_file

console = Console()

# Registry of available analyzers
ANALYZERS = [
    MaintainerAnalyzer(),
    CommunityAnalyzer(),
    SecurityAnalyzer(),
    SustainabilityAnalyzer(),
]


@click.group()
@click.version_option(__version__)
def main():
    """vigil — Predictive risk intelligence for open source dependencies."""


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--detail", "-d", is_flag=True, help="Show detailed signal breakdown.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def scan(file: str, detail: bool, as_json: bool):
    """Scan a dependency file for health risks."""
    path = Path(file)
    console.print(f"[dim]Parsing {path.name}...[/]")

    deps = parse_file(path)
    if not deps:
        console.print("[yellow]No dependencies found.[/]")
        return

    console.print(f"[dim]Found {len(deps)} dependencies. Analyzing...[/]")

    result = ScanResult(dependencies=deps, source_file=str(path))

    with PyPIClient() as pypi, GitHubClient() as github:
        ctx = AnalyzerContext(github=github, pypi=pypi)

        for dep in deps:
            profile = _analyze_dependency(dep.name, ctx)
            result.profiles[dep.name] = profile

    if as_json:
        _print_json(result)
    else:
        render_scan(result, console)
        if detail:
            for profile in sorted(
                result.profiles.values(), key=lambda p: p.risk_score, reverse=True
            ):
                render_detail(profile, console)


@main.command()
@click.argument("package")
def check(package: str):
    """Check a single package's health."""
    console.print(f"[dim]Checking {package}...[/]")

    with PyPIClient() as pypi, GitHubClient() as github:
        ctx = AnalyzerContext(github=github, pypi=pypi)
        profile = _analyze_dependency(package, ctx)

    render_detail(profile, console)


def _analyze_dependency(package: str, ctx: AnalyzerContext) -> HealthProfile:
    """Run all analyzers against a single package."""
    profile = HealthProfile(package=package)

    # Step 1: Get PyPI metadata
    pypi_info = ctx.pypi.get_package(package)
    if not pypi_info:
        profile.error = f"Package '{package}' not found on PyPI."
        return profile

    profile.version = pypi_info.version
    profile.repo_url = pypi_info.repo_url

    # Step 2: Get GitHub repo info if available
    repo_info = None
    if pypi_info.repo_url:
        parsed = parse_github_url(pypi_info.repo_url)
        if parsed:
            owner, name = parsed
            repo_info = ctx.github.get_repo(owner, name)

    # Step 3: Run all analyzers
    for analyzer in ANALYZERS:
        try:
            signals = analyzer.analyze(
                package, ctx, pypi_info=pypi_info, repo_info=repo_info
            )
            profile.signals.extend(signals)
        except Exception as e:
            console.print(f"[dim]  {analyzer.name} failed for {package}: {e}[/]")

    return profile


def _print_json(result: ScanResult):
    """Output scan result as JSON."""
    import json

    out = {
        "source_file": result.source_file,
        "scanned_at": result.scanned_at.isoformat(),
        "summary": {
            "total": len(result.dependencies),
            "critical": result.critical_count,
            "high": result.high_count,
            "unknown": result.unknown_count,
        },
        "packages": {},
    }

    for name, profile in result.profiles.items():
        out["packages"][name] = {
            "version": profile.version,
            "repo_url": profile.repo_url,
            "risk_score": round(profile.risk_score, 4),
            "risk_level": profile.risk_level.value,
            "error": profile.error,
            "signals": [
                {
                    "name": s.name,
                    "category": s.category.value,
                    "value": round(s.value, 4),
                    "confidence": round(s.confidence, 4),
                    "detail": s.detail,
                }
                for s in profile.signals
            ],
        }

    console.print_json(json.dumps(out, indent=2))
