"""CLI entry point for vigil."""

from __future__ import annotations

import time
from pathlib import Path

import click
from rich.console import Console

from vigil import __version__
from vigil.analyzers.base import AnalyzerContext
from vigil.analyzers.cascade import analyze_cascade
from vigil.analyzers.community import CommunityAnalyzer
from vigil.analyzers.maintainer import MaintainerAnalyzer
from vigil.analyzers.security import SecurityAnalyzer
from vigil.analyzers.sustainability import SustainabilityAnalyzer
from vigil.clients.github import CALLS_PER_PACKAGE, GitHubClient, RateLimitError, parse_github_url
from vigil.clients.pypi import PyPIClient
from vigil.config import VigilConfig, load_config, save_config
from vigil.models import HealthProfile, ScanResult
from vigil.output import render_detail, render_scan
from vigil.parsers import parse_file
from vigil.resolver import DependencyResolver

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
@click.option(
    "--cascade", "-c", is_flag=True,
    help="Analyze transitive dependency risk (uses PyPI only, no extra GitHub calls).",
)
def scan(file: str, detail: bool, as_json: bool, cascade: bool):
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
        _show_auth_status(github, len(deps))
        ctx = AnalyzerContext(github=github, pypi=pypi)

        resolver = DependencyResolver(pypi) if cascade else None

        for dep in deps:
            try:
                profile = _analyze_dependency(dep.name, ctx, resolver=resolver)
            except RateLimitError as e:
                console.print(f"\n[bold red]Rate limit hit[/] after {github.requests_made} requests.")
                wait = max(0, e.reset_at - int(time.time()))
                console.print(f"[yellow]Resets in {wait // 60}m {wait % 60}s.[/]")
                if not github.authenticated:
                    console.print(
                        "[yellow]Run [bold]vigil auth[/bold] to authenticate "
                        "(60 → 5,000 requests/hour).[/]"
                    )
                console.print(f"[dim]Partial results for {len(result.profiles)}/{len(deps)} packages below.[/]")
                break
            result.profiles[dep.name] = profile

        _show_budget_summary(github)
        if resolver:
            console.print(f"[dim]Resolved {resolver.packages_fetched} transitive packages from PyPI.[/]")

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
@click.option(
    "--cascade", "-c", is_flag=True,
    help="Analyze transitive dependency risk.",
)
def check(package: str, cascade: bool):
    """Check a single package's health."""
    console.print(f"[dim]Checking {package}...[/]")

    with PyPIClient() as pypi, GitHubClient() as github:
        _show_auth_status(github, 1)
        ctx = AnalyzerContext(github=github, pypi=pypi)
        resolver = DependencyResolver(pypi) if cascade else None

        try:
            profile = _analyze_dependency(package, ctx, resolver=resolver)
        except RateLimitError as e:
            console.print(f"[bold red]Rate limit hit.[/]")
            wait = max(0, e.reset_at - int(time.time()))
            console.print(f"[yellow]Resets in {wait // 60}m {wait % 60}s.[/]")
            if not github.authenticated:
                console.print(
                    "[yellow]Run [bold]vigil auth[/bold] to authenticate "
                    "(60 → 5,000 requests/hour).[/]"
                )
            return

        _show_budget_summary(github)
        if resolver:
            console.print(f"[dim]Resolved {resolver.packages_fetched} transitive packages from PyPI.[/]")

    render_detail(profile, console)


@main.group()
def auth():
    """Manage GitHub authentication for vigil."""


@auth.command("login")
@click.option("--token", "-t", prompt="GitHub personal access token",
              hide_input=True, help="GitHub PAT (no scopes needed for public repos).")
def auth_login(token: str):
    """Save a GitHub token for vigil to use.

    Tokens are stored in ~/.config/vigil/config.toml (mode 600).
    No scopes are needed — public repo data only.
    """
    token = token.strip()
    if not token:
        console.print("[red]Token cannot be empty.[/]")
        raise SystemExit(1)

    # Validate the token
    console.print("[dim]Validating token...[/]")
    with GitHubClient(token=token) as github:
        try:
            status = github.rate_limit_status()
        except Exception as e:
            console.print(f"[red]Token validation failed: {e}[/]")
            raise SystemExit(1)

    limit = status["limit"]
    remaining = status["remaining"]

    if limit <= 60:
        console.print(
            f"[yellow]Warning: token gives {limit} req/hr (same as unauthenticated). "
            "It may be invalid or expired.[/]"
        )
        if not click.confirm("Save anyway?"):
            return

    config = load_config()
    config.github_token = token
    save_config(config)

    console.print(f"[green]Token saved.[/] Rate limit: {remaining}/{limit} requests/hour.")
    console.print(f"[dim]Stored in ~/.config/vigil/config.toml[/]")


@auth.command("status")
def auth_status():
    """Show current authentication and rate limit status."""
    with GitHubClient() as github:
        if not github.authenticated:
            console.print("[yellow]Not authenticated.[/] Using unauthenticated rate limit (60 req/hr).")
            console.print("Run [bold]vigil auth login[/bold] to authenticate (→ 5,000 req/hr).")
            console.print()

        try:
            status = github.rate_limit_status()
        except Exception as e:
            console.print(f"[red]Could not check rate limit: {e}[/]")
            return

        remaining = status["remaining"]
        limit = status["limit"]
        reset_at = status["reset_at"]
        reset_in = max(0, reset_at - int(time.time()))

        console.print(f"[bold]Rate limit:[/] {remaining}/{limit} requests remaining")
        console.print(f"[bold]Resets in:[/] {reset_in // 60}m {reset_in % 60}s")
        console.print(f"[bold]Can scan:[/] ~{remaining // CALLS_PER_PACKAGE} packages")

        if github.authenticated:
            console.print(f"[green]Authenticated[/] (token from env or config)")
        else:
            console.print()
            console.print("[yellow]Tip:[/] Authenticate to increase limit from 60 → 5,000 req/hr:")
            console.print("  vigil auth login")


@auth.command("logout")
def auth_logout():
    """Remove saved GitHub token."""
    config = load_config()
    if not config.has_github_token:
        console.print("[dim]No saved token found.[/]")
        return

    config.github_token = None
    save_config(config)
    console.print("[green]Token removed.[/]")


def _show_auth_status(github: GitHubClient, package_count: int) -> None:
    """Show auth status and budget check before scanning."""
    if not github.authenticated:
        console.print(
            "[yellow]Warning:[/] No GitHub token. Rate limit: 60 requests/hour "
            f"(~{60 // CALLS_PER_PACKAGE} packages)."
        )
        console.print(
            "[yellow]Run [bold]vigil auth login[/bold] to authenticate "
            "(→ 5,000 req/hr, ~714 packages).[/]"
        )
        console.print()

    # Pre-flight budget check
    try:
        status = github.rate_limit_status()
        remaining = status["remaining"]
        needed = package_count * CALLS_PER_PACKAGE
        if remaining < needed:
            console.print(
                f"[yellow]Budget warning:[/] {remaining} requests remaining, "
                f"~{needed} needed for {package_count} packages."
            )
            if remaining < CALLS_PER_PACKAGE:
                reset_in = max(0, status["reset_at"] - int(time.time()))
                console.print(
                    f"[red]Insufficient budget.[/] Resets in {reset_in // 60}m {reset_in % 60}s."
                )
        else:
            console.print(
                f"[dim]Budget: {remaining} requests available "
                f"(~{needed} needed for {package_count} packages).[/]"
            )
    except Exception:
        pass  # Don't block scanning if rate_limit check fails


def _show_budget_summary(github: GitHubClient) -> None:
    """Show how many requests were consumed after scanning."""
    if github.requests_made > 0 and github.remaining is not None:
        console.print(
            f"[dim]Used {github.requests_made} API calls. "
            f"{github.remaining} remaining.[/]"
        )


def _analyze_dependency(
    package: str,
    ctx: AnalyzerContext,
    resolver: DependencyResolver | None = None,
) -> HealthProfile:
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
        except RateLimitError:
            raise  # Let caller handle rate limits
        except Exception as e:
            console.print(f"[dim]  {analyzer.name} failed for {package}: {e}[/]")

    # Step 4: Cascade risk analysis (if enabled)
    if resolver:
        try:
            tree = resolver.resolve(package)
            profile.dependency_tree = tree
            cascade_signals = analyze_cascade(tree, ctx.pypi)
            profile.signals.extend(cascade_signals)
        except Exception as e:
            console.print(f"[dim]  cascade analysis failed for {package}: {e}[/]")

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
        pkg_out = {
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
        if profile.dependency_tree:
            pkg_out["dependency_tree"] = _tree_to_dict(profile.dependency_tree)
        out["packages"][name] = pkg_out

    console.print_json(json.dumps(out, indent=2))


def _tree_to_dict(node) -> dict:
    """Convert DependencyNode to JSON-serializable dict."""
    d = {
        "package": node.package,
        "version": node.version,
        "depth": node.depth,
    }
    if node.risk_score is not None:
        d["risk_score"] = round(node.risk_score, 4)
    if node.children:
        d["children"] = [_tree_to_dict(c) for c in node.children]
    return d
