"""Report formatting for terminal output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from vigil.models import HealthProfile, RiskLevel, ScanResult, SignalCategory

RISK_COLORS = {
    RiskLevel.LOW: "green",
    RiskLevel.MODERATE: "yellow",
    RiskLevel.HIGH: "red",
    RiskLevel.CRITICAL: "bold red",
    RiskLevel.UNKNOWN: "dim",
}

RISK_ICONS = {
    RiskLevel.LOW: "[green]OK[/]",
    RiskLevel.MODERATE: "[yellow]WARN[/]",
    RiskLevel.HIGH: "[red]HIGH[/]",
    RiskLevel.CRITICAL: "[bold red]CRIT[/]",
    RiskLevel.UNKNOWN: "[dim]???[/]",
}


def render_scan(result: ScanResult, console: Console | None = None) -> None:
    """Render a full scan result to the terminal."""
    console = console or Console()

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]vigil[/] scan of [cyan]{result.source_file or 'dependencies'}[/]\n"
            f"{len(result.dependencies)} dependencies analyzed",
            title="vigil",
            border_style="blue",
        )
    )

    # Summary table
    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("Package", style="cyan", min_width=20)
    table.add_column("Risk", justify="center", width=6)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Top Concern", min_width=30)

    # Sort: worst first
    sorted_profiles = sorted(
        result.profiles.values(),
        key=lambda p: p.risk_score,
        reverse=True,
    )

    for profile in sorted_profiles:
        risk_icon = RISK_ICONS.get(profile.risk_level, "?")
        score_str = f"{profile.risk_score:.2f}" if profile.signals else "n/a"

        # Top concern = worst signal
        if profile.error:
            concern = f"[dim]{profile.error}[/]"
        elif profile.worst_signals:
            worst = profile.worst_signals[0]
            concern = worst.detail
        else:
            concern = "[dim]No data[/]"

        table.add_row(profile.package, risk_icon, score_str, concern)

    console.print(table)

    # Summary footer
    console.print()
    crits = result.critical_count
    highs = result.high_count
    unknowns = result.unknown_count
    total = len(result.profiles)

    if crits > 0:
        console.print(f"  [bold red]{crits}[/] critical", end="  ")
    if highs > 0:
        console.print(f"  [red]{highs}[/] high", end="  ")
    if unknowns > 0:
        console.print(f"  [dim]{unknowns}[/] unknown", end="  ")
    console.print(f"  [blue]{total}[/] total")
    console.print()


def render_detail(profile: HealthProfile, console: Console | None = None) -> None:
    """Render detailed signals for a single package."""
    console = console or Console()

    risk_color = RISK_COLORS.get(profile.risk_level, "white")
    console.print(
        Panel(
            f"[bold]{profile.package}[/] "
            f"[{risk_color}]{profile.risk_level.value.upper()}[/] "
            f"(score: {profile.risk_score:.3f})\n"
            f"repo: {profile.repo_url or 'unknown'}",
            border_style=risk_color,
        )
    )

    if not profile.signals:
        console.print("  [dim]No signals collected.[/]")
        return

    for category in SignalCategory:
        cat_signals = profile.signals_by_category(category)
        if not cat_signals:
            continue

        console.print(f"  [bold]{category.value}[/]")
        for s in sorted(cat_signals, key=lambda x: x.value):
            bar = _health_bar(s.value)
            conf = f"[dim](conf: {s.confidence:.0%})[/]"
            console.print(f"    {bar} {s.name}: {s.detail} {conf}")
        console.print()


def _health_bar(value: float, width: int = 10) -> str:
    """Visual health bar."""
    filled = round(value * width)
    if value >= 0.7:
        color = "green"
    elif value >= 0.4:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/]"
