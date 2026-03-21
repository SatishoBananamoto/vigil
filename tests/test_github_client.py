"""Tests for GitHubClient budget tracking and token resolution."""

import time

import httpx
import pytest
import respx

from vigil.clients.github import CALLS_PER_PACKAGE, GitHubClient, RateLimitError


class TestBudgetTracking:
    @respx.mock
    def test_tracks_remaining_from_headers(self):
        respx.get("https://api.github.com/repos/test/repo").mock(
            return_value=httpx.Response(
                200,
                json={"full_name": "test/repo"},
                headers={
                    "x-ratelimit-remaining": "42",
                    "x-ratelimit-limit": "60",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        with GitHubClient(token="fake") as client:
            client._get("/repos/test/repo")
            assert client.remaining == 42
            assert client.limit == 60
            assert client.requests_made == 1

    @respx.mock
    def test_requests_made_increments(self):
        respx.get("https://api.github.com/repos/a/b").mock(
            return_value=httpx.Response(
                200,
                json={},
                headers={"x-ratelimit-remaining": "100", "x-ratelimit-limit": "5000"},
            )
        )
        respx.get("https://api.github.com/repos/c/d").mock(
            return_value=httpx.Response(
                200,
                json={},
                headers={"x-ratelimit-remaining": "99", "x-ratelimit-limit": "5000"},
            )
        )

        with GitHubClient(token="fake") as client:
            client._get("/repos/a/b")
            client._get("/repos/c/d")
            assert client.requests_made == 2
            assert client.remaining == 99

    @respx.mock
    def test_cache_hit_doesnt_count(self):
        respx.get("https://api.github.com/repos/a/b").mock(
            return_value=httpx.Response(
                200,
                json={"cached": True},
                headers={"x-ratelimit-remaining": "50", "x-ratelimit-limit": "60"},
            )
        )

        with GitHubClient(token="fake") as client:
            client._get("/repos/a/b")
            client._get("/repos/a/b")  # cache hit
            assert client.requests_made == 1

    @respx.mock
    def test_rate_limit_error_raised(self):
        reset_time = int(time.time()) + 3600
        respx.get("https://api.github.com/repos/a/b").mock(
            return_value=httpx.Response(
                403,
                json={"message": "rate limit exceeded"},
                headers={
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-limit": "60",
                    "x-ratelimit-reset": str(reset_time),
                },
            )
        )

        with GitHubClient(token="fake") as client:
            with pytest.raises(RateLimitError) as exc_info:
                client._get("/repos/a/b")
            assert exc_info.value.reset_at == reset_time


class TestCanScan:
    @respx.mock
    def test_can_scan_with_budget(self):
        respx.get("https://api.github.com/repos/a/b").mock(
            return_value=httpx.Response(
                200,
                json={},
                headers={"x-ratelimit-remaining": "100", "x-ratelimit-limit": "5000"},
            )
        )

        with GitHubClient(token="fake") as client:
            client._get("/repos/a/b")  # populate remaining
            can, needed = client.can_scan(10)
            assert can is True
            assert needed == 10 * CALLS_PER_PACKAGE

    @respx.mock
    def test_cannot_scan_low_budget(self):
        respx.get("https://api.github.com/repos/a/b").mock(
            return_value=httpx.Response(
                200,
                json={},
                headers={"x-ratelimit-remaining": "5", "x-ratelimit-limit": "60"},
            )
        )

        with GitHubClient(token="fake") as client:
            client._get("/repos/a/b")
            can, needed = client.can_scan(10)
            assert can is False

    def test_unknown_budget_is_optimistic(self):
        # Before any request, remaining is None — be optimistic
        with GitHubClient(token="fake") as client:
            can, needed = client.can_scan(5)
            assert can is True


class TestTokenResolution:
    def test_explicit_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with GitHubClient(token="explicit") as client:
            assert client.authenticated is True

    def test_no_token(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("vigil.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        with GitHubClient() as client:
            assert client.authenticated is False
