"""Tests for config module and token resolution."""

import os
from pathlib import Path

import pytest

from vigil.config import VigilConfig, load_config, save_config, resolve_github_token


class TestVigilConfig:
    def test_has_github_token_when_set(self):
        c = VigilConfig(github_token="ghp_test123")
        assert c.has_github_token is True

    def test_has_github_token_when_empty(self):
        c = VigilConfig(github_token="")
        assert c.has_github_token is False

    def test_has_github_token_when_none(self):
        c = VigilConfig()
        assert c.has_github_token is False


class TestSaveLoadConfig:
    def test_roundtrip(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("vigil.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", config_file)

        original = VigilConfig(github_token="ghp_roundtrip_test")
        save_config(original)

        assert config_file.exists()
        # Check file permissions (600 = owner read/write only)
        assert oct(config_file.stat().st_mode)[-3:] == "600"

        loaded = load_config()
        assert loaded.github_token == "ghp_roundtrip_test"

    def test_load_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vigil.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        config = load_config()
        assert config.github_token is None

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        nested = tmp_path / "deep" / "nested"
        monkeypatch.setattr("vigil.config.CONFIG_DIR", nested)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", nested / "config.toml")

        save_config(VigilConfig(github_token="ghp_test"))
        assert (nested / "config.toml").exists()

    def test_save_empty_token(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("vigil.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", config_file)

        save_config(VigilConfig(github_token=None))
        loaded = load_config()
        assert loaded.github_token is None


class TestResolveGithubToken:
    def test_explicit_wins(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        assert resolve_github_token("explicit_token") == "explicit_token"

    def test_env_beats_config(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("vigil.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", config_file)

        save_config(VigilConfig(github_token="config_token"))
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        assert resolve_github_token() == "env_token"

    def test_config_fallback(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("vigil.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", config_file)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        save_config(VigilConfig(github_token="config_token"))
        assert resolve_github_token() == "config_token"

    def test_no_token_anywhere(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vigil.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        assert resolve_github_token() is None
