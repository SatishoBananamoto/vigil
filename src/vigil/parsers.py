"""Parse dependency files into Dependency objects."""

from __future__ import annotations

import re
from pathlib import Path

from vigil.models import Dependency

# Matches: package, package==1.0, package>=1.0,<2.0, package[extra1,extra2]>=1.0
_REQ_PATTERN = re.compile(
    r"^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)"  # package name
    r"(\[([^\]]+)\])?"  # optional extras
    r"(.*)?$"  # version spec (everything else)
)


def parse_requirements_txt(path: str | Path) -> list[Dependency]:
    """Parse a requirements.txt file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")

    deps = []
    for line in path.read_text().splitlines():
        line = line.strip()
        # Skip blanks, comments, options
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        dep = _parse_requirement_line(line)
        if dep:
            deps.append(dep)
    return deps


def parse_pyproject_toml(path: str | Path) -> list[Dependency]:
    """Parse dependencies from pyproject.toml [project.dependencies]."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"pyproject.toml not found: {path}")

    # Minimal TOML parsing — we only need [project] dependencies
    # Using stdlib tomllib (3.11+) or fallback
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            raise RuntimeError(
                "Python 3.11+ or 'tomli' package required for pyproject.toml parsing"
            )

    with open(path, "rb") as f:
        data = tomllib.load(f)

    raw_deps = data.get("project", {}).get("dependencies", [])
    deps = []
    for line in raw_deps:
        dep = _parse_requirement_line(line)
        if dep:
            deps.append(dep)
    return deps


def parse_file(path: str | Path) -> list[Dependency]:
    """Auto-detect file type and parse dependencies."""
    path = Path(path)
    name = path.name.lower()

    if name == "pyproject.toml":
        return parse_pyproject_toml(path)
    if name in ("requirements.txt", "requirements.in") or name.startswith("requirements"):
        return parse_requirements_txt(path)

    # Default: try as requirements.txt format
    return parse_requirements_txt(path)


def _parse_requirement_line(line: str) -> Dependency | None:
    """Parse a single requirement line."""
    # Strip inline comments
    if " #" in line:
        line = line[: line.index(" #")]
    line = line.strip()

    # Skip environment markers for now (;python_version etc)
    if ";" in line:
        line = line[: line.index(";")].strip()

    match = _REQ_PATTERN.match(line)
    if not match:
        return None

    name = match.group(1)
    extras_str = match.group(4)
    version_spec = (match.group(5) or "").strip() or None

    extras = [e.strip() for e in extras_str.split(",")] if extras_str else []

    return Dependency(name=name, version_spec=version_spec, extras=extras)
