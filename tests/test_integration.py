"""Integration tests — end-to-end scan + report pipeline.

These test with mocked HTTP clients to avoid real API calls.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from click.testing import CliRunner

from vigil.cli import main
from vigil.clients.pypi import PyPIPackageInfo, PyPIRelease


def _mock_pypi_info(name, days_since=30, total_releases=10, repo_url=None):
    """Create a mock PyPIPackageInfo."""
    releases = [
        PyPIRelease(
            version=f"1.0.{i}",
            upload_time=datetime.now(timezone.utc) - timedelta(days=days_since + i * 30),
            yanked=False,
        )
        for i in range(total_releases)
    ]
    return PyPIPackageInfo(
        name=name,
        version="1.0.0",
        releases=releases,
        home_page=repo_url or "",
        project_urls={"Source": repo_url} if repo_url else {},
    )


class TestScanPipeline:
    """Test the full scan pipeline with mocked APIs."""

    def test_scan_requirements_txt(self, tmp_path):
        """Scan a requirements.txt file end-to-end."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests\nclick\n")

        runner = CliRunner()

        with patch("vigil.cli.PyPIClient") as mock_pypi_cls, \
             patch("vigil.cli.GitHubClient") as mock_gh_cls:

            mock_pypi = MagicMock()
            mock_pypi.__enter__ = MagicMock(return_value=mock_pypi)
            mock_pypi.__exit__ = MagicMock(return_value=False)
            mock_pypi.get_package.return_value = _mock_pypi_info("test")
            mock_pypi_cls.return_value = mock_pypi

            mock_gh = MagicMock()
            mock_gh.__enter__ = MagicMock(return_value=mock_gh)
            mock_gh.__exit__ = MagicMock(return_value=False)
            mock_gh.authenticated = False
            mock_gh.requests_made = 0
            mock_gh.remaining = None
            mock_gh_cls.return_value = mock_gh

            result = runner.invoke(main, ["scan", str(req_file)])
            assert result.exit_code == 0
            assert "2 dependencies" in result.output or "total" in result.output


class TestReportPipeline:
    """Test the report command output format."""

    def test_report_produces_markdown(self, tmp_path):
        """Report command generates valid markdown."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("testpkg\n")
        report_file = tmp_path / "report.md"

        runner = CliRunner()

        with patch("vigil.cli.PyPIClient") as mock_pypi_cls, \
             patch("vigil.cli.GitHubClient") as mock_gh_cls:

            mock_pypi = MagicMock()
            mock_pypi.__enter__ = MagicMock(return_value=mock_pypi)
            mock_pypi.__exit__ = MagicMock(return_value=False)
            mock_pypi.get_package.return_value = _mock_pypi_info("testpkg")
            mock_pypi_cls.return_value = mock_pypi

            mock_gh = MagicMock()
            mock_gh.__enter__ = MagicMock(return_value=mock_gh)
            mock_gh.__exit__ = MagicMock(return_value=False)
            mock_gh.authenticated = False
            mock_gh.requests_made = 0
            mock_gh.remaining = None
            mock_gh_cls.return_value = mock_gh

            result = runner.invoke(main, ["report", str(req_file), "-o", str(report_file)])
            assert result.exit_code == 0

            content = report_file.read_text()
            assert "# " in content  # Has heading
            assert "| Package |" in content  # Has table header
            assert "**Summary:**" in content  # Has summary


class TestCheckCommand:
    """Test the check command."""

    def test_check_json_output(self):
        """Check --json produces valid JSON."""
        runner = CliRunner()

        with patch("vigil.cli.PyPIClient") as mock_pypi_cls, \
             patch("vigil.cli.GitHubClient") as mock_gh_cls:

            mock_pypi = MagicMock()
            mock_pypi.__enter__ = MagicMock(return_value=mock_pypi)
            mock_pypi.__exit__ = MagicMock(return_value=False)
            mock_pypi.get_package.return_value = _mock_pypi_info("testpkg")
            mock_pypi_cls.return_value = mock_pypi

            mock_gh = MagicMock()
            mock_gh.__enter__ = MagicMock(return_value=mock_gh)
            mock_gh.__exit__ = MagicMock(return_value=False)
            mock_gh.authenticated = False
            mock_gh.requests_made = 0
            mock_gh.remaining = None
            mock_gh.get_repo.return_value = None
            mock_gh_cls.return_value = mock_gh

            result = runner.invoke(main, ["check", "testpkg", "--json"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert "package" in data
            assert "risk_score" in data
            assert "signals" in data
