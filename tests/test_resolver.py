"""Tests for dependency tree resolution."""

from unittest.mock import MagicMock

from vigil.clients.pypi import PyPIPackageInfo, PyPIRelease
from vigil.resolver import DependencyResolver, normalize_name, parse_requires_dist


class TestParseRequiresDist:
    def test_simple_deps(self):
        specs = ["requests>=2.28", "click>=8.1", "rich>=13.0"]
        names = parse_requires_dist(specs)
        assert names == ["requests", "click", "rich"]

    def test_filters_extras(self):
        specs = [
            "urllib3>=1.21",
            'PySocks!=1.5.7; extra == "socks"',
            'chardet>=3.0; extra == "use_chardet"',
        ]
        names = parse_requires_dist(specs)
        assert names == ["urllib3"]

    def test_keeps_environment_markers(self):
        specs = [
            'typing-extensions>=4.0; python_version < "3.11"',
            'win32-setctime>=1.0; sys_platform == "win32"',
        ]
        names = parse_requires_dist(specs)
        assert names == ["typing-extensions", "win32-setctime"]

    def test_deduplicates(self):
        specs = ["requests>=2.28", "requests>=2.20"]
        names = parse_requires_dist(specs)
        assert names == ["requests"]

    def test_normalizes_names(self):
        specs = ["My_Package>=1.0", "another.package>=2.0"]
        names = parse_requires_dist(specs)
        assert names == ["my-package", "another-package"]

    def test_empty_list(self):
        assert parse_requires_dist([]) == []

    def test_version_specifiers(self):
        specs = ["certifi>=2017.4.17", "charset-normalizer<4,>=2", "idna<4,>=2.5"]
        names = parse_requires_dist(specs)
        assert names == ["certifi", "charset-normalizer", "idna"]


class TestNormalizeName:
    def test_lowercase(self):
        assert normalize_name("Requests") == "requests"

    def test_underscores(self):
        assert normalize_name("my_package") == "my-package"

    def test_dots(self):
        assert normalize_name("my.package") == "my-package"

    def test_mixed(self):
        assert normalize_name("My_Cool.Package") == "my-cool-package"


def _mock_pypi(packages: dict[str, list[str]]) -> MagicMock:
    """Create a mock PyPIClient that returns packages with given requires_dist."""
    client = MagicMock()

    def get_package(name):
        name = normalize_name(name)
        if name not in packages:
            return None
        return PyPIPackageInfo(
            name=name,
            version="1.0.0",
            requires_dist=packages[name],
        )

    client.get_package = get_package
    return client


class TestDependencyResolver:
    def test_simple_tree(self):
        pypi = _mock_pypi({
            "requests": ["urllib3>=1.21", "certifi>=2017"],
            "urllib3": [],
            "certifi": [],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("requests")

        assert tree.package == "requests"
        assert tree.depth == 0
        assert len(tree.children) == 2
        assert tree.children[0].package == "urllib3"
        assert tree.children[0].depth == 1
        assert tree.children[1].package == "certifi"
        assert tree.children[1].depth == 1

    def test_transitive_deps(self):
        pypi = _mock_pypi({
            "flask": ["jinja2>=3.0", "werkzeug>=2.0"],
            "jinja2": ["markupsafe>=2.0"],
            "werkzeug": ["markupsafe>=2.0"],
            "markupsafe": [],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("flask")

        assert tree.package == "flask"
        assert len(tree.children) == 2
        # jinja2 has markupsafe as child
        jinja2 = tree.children[0]
        assert jinja2.package == "jinja2"
        assert len(jinja2.children) == 1
        assert jinja2.children[0].package == "markupsafe"
        assert jinja2.children[0].depth == 2

    def test_cycle_detection(self):
        pypi = _mock_pypi({
            "a": ["b>=1.0"],
            "b": ["a>=1.0"],  # cycle!
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("a")

        assert tree.package == "a"
        assert len(tree.children) == 1
        b = tree.children[0]
        assert b.package == "b"
        # b's child should be 'a' but as a leaf (cycle detected)
        assert len(b.children) == 1
        assert b.children[0].package == "a"
        assert b.children[0].children == []  # no infinite recursion

    def test_max_depth(self):
        pypi = _mock_pypi({
            "a": ["b>=1.0"],
            "b": ["c>=1.0"],
            "c": ["d>=1.0"],
            "d": ["e>=1.0"],
            "e": [],
        })
        resolver = DependencyResolver(pypi, max_depth=2)
        tree = resolver.resolve("a")

        assert tree.package == "a"
        assert tree.depth == 0
        b = tree.children[0]
        assert b.depth == 1
        c = b.children[0]
        assert c.depth == 2
        # d should be a leaf (depth 3 > max_depth 2)
        assert len(c.children) == 1
        d = c.children[0]
        assert d.children == []  # stopped at max depth

    def test_unknown_package(self):
        pypi = _mock_pypi({
            "mypackage": ["nonexistent>=1.0"],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("mypackage")

        assert len(tree.children) == 1
        assert tree.children[0].package == "nonexistent"
        assert tree.children[0].children == []

    def test_pypi_fetch_deduplication(self):
        pypi = _mock_pypi({
            "a": ["shared>=1.0"],
            "b": ["shared>=1.0"],
            "shared": [],
        })
        resolver = DependencyResolver(pypi)
        resolver.resolve("a")
        resolver.resolve("b")
        # shared should only be fetched once
        assert resolver.packages_fetched == 3  # a, shared, b

    def test_filters_extras_in_tree(self):
        pypi = _mock_pypi({
            "requests": ["urllib3>=1.21", 'PySocks>=1.5; extra == "socks"'],
            "urllib3": [],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("requests")

        assert len(tree.children) == 1
        assert tree.children[0].package == "urllib3"

    def test_total_nodes(self):
        pypi = _mock_pypi({
            "root": ["a>=1.0", "b>=1.0"],
            "a": ["c>=1.0"],
            "b": [],
            "c": [],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("root")
        assert tree.total_nodes == 4  # root, a, b, c

    def test_flatten(self):
        pypi = _mock_pypi({
            "root": ["a>=1.0", "b>=1.0"],
            "a": ["c>=1.0"],
            "b": [],
            "c": [],
        })
        resolver = DependencyResolver(pypi)
        tree = resolver.resolve("root")
        flat = tree.flatten()
        names = [n.package for n in flat]
        assert names == ["root", "a", "b", "c"]
