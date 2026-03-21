"""Transitive dependency tree resolution via PyPI requires_dist."""

from __future__ import annotations

import re

from vigil.clients.pypi import PyPIClient, PyPIPackageInfo
from vigil.models import DependencyNode

# Safety limits
DEFAULT_MAX_DEPTH = 3
MAX_TOTAL_NODES = 200

# PEP 508 package name pattern
_NAME_RE = re.compile(r'^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)')


def normalize_name(name: str) -> str:
    """PEP 503 canonical package name."""
    return re.sub(r'[-_.]+', '-', name).lower()


def parse_requires_dist(specs: list[str]) -> list[str]:
    """Extract package names from requires_dist, filtering extras-only deps.

    Keeps environment-conditional deps (python_version, sys_platform, etc.)
    because they're runtime deps. Skips extras-only deps because they're
    optional and not installed by default.
    """
    names = []
    seen = set()
    for spec in specs:
        spec = spec.strip()
        # Skip extras-only dependencies
        if 'extra ==' in spec or "extra ==" in spec:
            continue
        match = _NAME_RE.match(spec)
        if match:
            normalized = normalize_name(match.group(1))
            if normalized not in seen:
                seen.add(normalized)
                names.append(normalized)
    return names


class DependencyResolver:
    """Resolves transitive dependency trees using PyPI requires_dist.

    Uses two layers of deduplication:
    - _pkg_cache: PyPI fetch deduplication (same package fetched once)
    - ancestors frozenset: cycle detection per branch path
    """

    def __init__(self, pypi: PyPIClient, max_depth: int = DEFAULT_MAX_DEPTH):
        self._pypi = pypi
        self._max_depth = max_depth
        self._pkg_cache: dict[str, tuple[PyPIPackageInfo | None, list[str]]] = {}
        self._total_resolved: int = 0

    @property
    def packages_fetched(self) -> int:
        return len(self._pkg_cache)

    def resolve(self, package: str) -> DependencyNode:
        """Resolve the full dependency tree for a package.

        The root node (depth 0) is the package itself.
        Children are its direct runtime dependencies from requires_dist.
        """
        self._total_resolved = 0
        return self._resolve(package, depth=0, ancestors=frozenset())

    def _fetch_package(self, name: str) -> tuple[PyPIPackageInfo | None, list[str]]:
        """Fetch PyPI info and parse child dependencies. Cached."""
        if name in self._pkg_cache:
            return self._pkg_cache[name]
        info = self._pypi.get_package(name)
        children = parse_requires_dist(info.requires_dist) if info else []
        self._pkg_cache[name] = (info, children)
        return info, children

    def _resolve(
        self, package: str, depth: int, ancestors: frozenset[str]
    ) -> DependencyNode:
        normalized = normalize_name(package)

        # Cycle detection
        if normalized in ancestors:
            return DependencyNode(package=normalized, depth=depth)

        # Depth limit
        if depth > self._max_depth:
            return DependencyNode(package=normalized, depth=depth)

        # Global node limit (prevent runaway resolution on huge trees)
        if self._total_resolved >= MAX_TOTAL_NODES:
            return DependencyNode(package=normalized, depth=depth)

        self._total_resolved += 1

        info, child_names = self._fetch_package(normalized)
        if not info:
            return DependencyNode(package=normalized, depth=depth)

        # Recurse into children
        new_ancestors = ancestors | {normalized}
        children = []
        for child_name in child_names:
            child_node = self._resolve(child_name, depth + 1, new_ancestors)
            children.append(child_node)

        return DependencyNode(
            package=normalized,
            version=info.version,
            depth=depth,
            children=children,
        )
