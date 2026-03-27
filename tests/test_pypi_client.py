"""Tests for PyPI client — repo URL detection."""

from vigil.clients.pypi import PyPIPackageInfo


class TestRepoUrl:
    def test_source_key(self):
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"Source": "https://github.com/org/repo"})
        assert info.repo_url == "https://github.com/org/repo"

    def test_repository_key(self):
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"Repository": "https://github.com/org/repo"})
        assert info.repo_url == "https://github.com/org/repo"

    def test_lowercase_repository(self):
        """jsonref uses lowercase 'repository'."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"repository": "https://github.com/org/repo"})
        assert info.repo_url == "https://github.com/org/repo"

    def test_lowercase_source(self):
        """scikit-learn, scipy use lowercase 'source'."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"source": "https://github.com/org/repo"})
        assert info.repo_url == "https://github.com/org/repo"

    def test_homepage_github(self):
        """sniffio has GitHub URL under 'Homepage'."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"Homepage": "https://github.com/org/repo"})
        assert info.repo_url == "https://github.com/org/repo"

    def test_homepage_non_github(self):
        """Non-GitHub homepage shouldn't be returned."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"Homepage": "https://example.com"})
        assert info.repo_url is None

    def test_home_page_field(self):
        """Fall back to home_page field."""
        info = PyPIPackageInfo(name="test", version="1.0", home_page="https://github.com/org/repo")
        assert info.repo_url == "https://github.com/org/repo"

    def test_gitlab(self):
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={"Source": "https://gitlab.com/org/repo"})
        assert info.repo_url == "https://gitlab.com/org/repo"

    def test_no_urls(self):
        info = PyPIPackageInfo(name="test", version="1.0")
        assert info.repo_url is None

    def test_source_preferred_over_homepage(self):
        """Explicit source key takes priority over homepage."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={
            "Homepage": "https://example.com",
            "Source": "https://github.com/org/repo",
        })
        assert info.repo_url == "https://github.com/org/repo"

    def test_any_github_url_as_fallback(self):
        """If no known key matches, any GitHub URL in project_urls works."""
        info = PyPIPackageInfo(name="test", version="1.0", project_urls={
            "Bug Tracker": "https://github.com/org/repo/issues",
        })
        assert "github.com" in info.repo_url
