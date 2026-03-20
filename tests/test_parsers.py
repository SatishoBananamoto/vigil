"""Tests for dependency file parsers."""

import tempfile
from pathlib import Path

from vigil.parsers import parse_file, parse_requirements_txt, _parse_requirement_line


class TestParseRequirementLine:
    def test_simple(self):
        dep = _parse_requirement_line("requests")
        assert dep.name == "requests"
        assert dep.version_spec is None

    def test_pinned(self):
        dep = _parse_requirement_line("requests==2.31.0")
        assert dep.name == "requests"
        assert dep.version_spec == "==2.31.0"

    def test_range(self):
        dep = _parse_requirement_line("flask>=2.0,<3.0")
        assert dep.name == "flask"
        assert dep.version_spec == ">=2.0,<3.0"

    def test_extras(self):
        dep = _parse_requirement_line("httpx[http2]>=0.27")
        assert dep.name == "httpx"
        assert dep.extras == ["http2"]
        assert dep.version_spec == ">=0.27"

    def test_multiple_extras(self):
        dep = _parse_requirement_line("package[extra1,extra2]")
        assert dep.extras == ["extra1", "extra2"]

    def test_inline_comment(self):
        dep = _parse_requirement_line("requests>=2.0 # http library")
        assert dep.name == "requests"
        assert dep.version_spec == ">=2.0"

    def test_env_marker_stripped(self):
        dep = _parse_requirement_line('pywin32; sys_platform == "win32"')
        assert dep.name == "pywin32"

    def test_blank_returns_none(self):
        assert _parse_requirement_line("") is None

    def test_comment_returns_none(self):
        assert _parse_requirement_line("# comment") is None


class TestParseRequirementsTxt:
    def test_basic_file(self):
        content = """
# Web framework
flask>=2.0
requests==2.31.0

# Utils
click>=8.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()
            deps = parse_requirements_txt(f.name)

        assert len(deps) == 3
        assert deps[0].name == "flask"
        assert deps[1].name == "requests"
        assert deps[2].name == "click"

    def test_skips_options(self):
        content = """
--index-url https://pypi.org/simple
-r base.txt
requests
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()
            deps = parse_requirements_txt(f.name)

        assert len(deps) == 1
        assert deps[0].name == "requests"


class TestParseFile:
    def test_autodetect_requirements(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="requirements", delete=False
        ) as f:
            f.write("requests\nflask\n")
            f.flush()
            deps = parse_file(f.name)

        assert len(deps) == 2
