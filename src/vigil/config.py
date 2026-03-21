"""Configuration management for vigil."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Default config location following XDG
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "vigil"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class VigilConfig:
    """Vigil configuration loaded from config.toml."""

    github_token: str | None = None

    @property
    def has_github_token(self) -> bool:
        return self.github_token is not None and len(self.github_token) > 0


def load_config() -> VigilConfig:
    """Load config from disk. Returns defaults if no config file exists."""
    config = VigilConfig()

    if not CONFIG_FILE.exists():
        return config

    try:
        import tomllib
    except ModuleNotFoundError:
        # Python < 3.11 fallback — parse the simple TOML we write
        return _parse_simple_toml(CONFIG_FILE, config)

    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        config.github_token = data.get("github_token")
    except Exception:
        pass

    return config


def save_config(config: VigilConfig) -> None:
    """Write config to disk as TOML."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    if config.github_token:
        lines.append(f'github_token = "{config.github_token}"')
    CONFIG_FILE.write_text("\n".join(lines) + "\n")
    # Restrict permissions — token is sensitive
    CONFIG_FILE.chmod(0o600)


def resolve_github_token(explicit: str | None = None) -> str | None:
    """Resolve GitHub token with priority: explicit > env var > config file."""
    if explicit:
        return explicit
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        return env_token
    return load_config().github_token


def _parse_simple_toml(path: Path, config: VigilConfig) -> VigilConfig:
    """Minimal TOML parser for the simple key=value format we write."""
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"')
            if key == "github_token":
                config.github_token = value
    except Exception:
        pass
    return config
