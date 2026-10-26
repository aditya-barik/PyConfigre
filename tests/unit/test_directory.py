"""Test suite for pyconfigre.directory — directory loading and ConfigNamespace.

Covers ConfigNamespace attribute/subscript access, read-only enforcement,
load_directory with recursive/hidden/extension options, and pipeline
integration via RawConfigBuilder.from_directory().
"""

from pathlib import Path

import pytest

from pyconfigre import RawConfigBuilder
from pyconfigre.directory import ConfigNamespace, load_directory
from pyconfigre.exceptions import ConfigLoadError, ConfigNotFoundError


class TestConfigNamespace:
    """Tests for ConfigNamespace wrapper."""

    def test_attribute_access(self) -> None:
        """Attribute access returns values from internal dict."""
        ns = ConfigNamespace({"database": {"host": "localhost"}})
        assert ns.database == {"host": "localhost"}

    def test_subscript_access(self) -> None:
        """Subscript access returns values from internal dict."""
        ns = ConfigNamespace({"server": {"port": 8080}})
        assert ns["server"] == {"port": 8080}

    def test_to_dict(self) -> None:
        """to_dict() returns a plain dict copy."""
        data = {"a": 1, "b": 2}
        ns = ConfigNamespace(data)
        result = ns.to_dict()
        assert result == data
        assert result is not data

    def test_contains(self) -> None:
        """'in' operator checks key presence."""
        ns = ConfigNamespace({"key": "val"})
        assert "key" in ns
        assert "missing" not in ns

    def test_repr(self) -> None:
        """repr includes class name and data."""
        ns = ConfigNamespace({"x": 1})
        assert "ConfigNamespace" in repr(ns)
        assert "'x': 1" in repr(ns)

    def test_read_only_enforcement(self) -> None:
        """Setting attributes raises AttributeError."""
        ns = ConfigNamespace({"key": "val"})
        with pytest.raises(AttributeError, match="read-only"):
            ns.key = "new_val"

    def test_missing_attribute_raises(self) -> None:
        """Accessing a missing attribute raises AttributeError."""
        ns = ConfigNamespace({})
        with pytest.raises(AttributeError, match="no attribute"):
            _ = ns.missing_key

    def test_missing_subscript_raises(self) -> None:
        """Accessing a missing subscript raises KeyError."""
        ns = ConfigNamespace({})
        with pytest.raises(KeyError):
            _ = ns["missing"]


class TestLoadDirectory:
    """Tests for load_directory()."""

    def test_loads_yaml_and_json(self, temp_dir: Path) -> None:
        """Loads multiple file formats from a directory."""
        (temp_dir / "database.yaml").write_text("host: localhost\nport: 5432\n")
        (temp_dir / "server.json").write_text('{"port": 8080}')

        ns = load_directory(temp_dir)
        assert ns.database == {"host": "localhost", "port": 5432}
        assert ns.server == {"port": 8080}

    def test_missing_directory_raises(self) -> None:
        """Non-existent path raises ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError, match="Directory not found"):
            load_directory("/nonexistent/path/xyz")

    def test_non_directory_path_raises(self, temp_dir: Path) -> None:
        """File path (not directory) raises ConfigLoadError."""
        f = temp_dir / "file.yaml"
        f.write_text("key: val\n")
        with pytest.raises(ConfigLoadError, match="Not a directory"):
            load_directory(f)

    def test_unknown_extensions_skip(self, temp_dir: Path) -> None:
        """Files with unknown extensions are silently skipped."""
        (temp_dir / "config.yaml").write_text("key: val\n")
        (temp_dir / "readme.txt").write_text("hello")

        ns = load_directory(temp_dir, unknown_extensions="skip")
        assert "config" in ns
        assert "readme" not in ns

    def test_unknown_extensions_raise(self, temp_dir: Path) -> None:
        """Files with unknown extensions raise ValueError."""
        (temp_dir / "readme.txt").write_text("hello")
        with pytest.raises(ValueError, match="Unsupported"):
            load_directory(temp_dir, unknown_extensions="raise")

    def test_recursive_true(self, temp_dir: Path) -> None:
        """Recursive mode finds files in subdirectories."""
        sub = temp_dir / "sub"
        sub.mkdir()
        (sub / "nested.yaml").write_text("deep: true\n")

        ns = load_directory(temp_dir, recursive=True)
        assert ns.nested == {"deep": True}

    def test_recursive_false(self, temp_dir: Path) -> None:
        """Non-recursive mode ignores subdirectories."""
        sub = temp_dir / "sub"
        sub.mkdir()
        (sub / "nested.yaml").write_text("deep: true\n")
        (temp_dir / "top.yaml").write_text("shallow: true\n")

        ns = load_directory(temp_dir, recursive=False)
        assert "top" in ns
        assert "nested" not in ns

    def test_hidden_file_skipped(self, temp_dir: Path) -> None:
        """Hidden files (dot-prefixed) are skipped by default."""
        (temp_dir / ".secret.yaml").write_text("key: secret\n")
        (temp_dir / "public.yaml").write_text("key: public\n")

        ns = load_directory(temp_dir)
        assert "public" in ns
        assert ".secret" not in ns

    def test_hidden_file_included(self, temp_dir: Path) -> None:
        """Hidden files are loaded when skip_hidden=False."""
        (temp_dir / ".secret.yaml").write_text("key: secret\n")

        ns = load_directory(temp_dir, skip_hidden=False)
        assert ".secret" in ns

    def test_empty_directory(self, temp_dir: Path) -> None:
        """Empty directory returns empty namespace."""
        ns = load_directory(temp_dir)
        assert ns.to_dict() == {}


class TestFromDirectoryPipeline:
    """Tests for RawConfigBuilder.from_directory() integration."""

    def test_pipeline_integration(self, temp_dir: Path) -> None:
        """from_directory merges loaded configs into the pipeline."""
        (temp_dir / "database.yaml").write_text("host: localhost\nport: 5432\n")
        (temp_dir / "server.json").write_text('{"port": 8080}')

        result = RawConfigBuilder().from_directory(temp_dir).build_dict()
        assert result["database"] == {"host": "localhost", "port": 5432}
        assert result["server"] == {"port": 8080}

    def test_from_directory_with_when_false(self, temp_dir: Path) -> None:
        """from_directory skips when condition is False."""
        (temp_dir / "config.yaml").write_text("key: val\n")
        result = (
            RawConfigBuilder()
            .from_directory(temp_dir, when=lambda: False)
            .build_dict()
        )
        assert result == {}

    def test_from_directory_with_when_true(self, temp_dir: Path) -> None:
        """from_directory loads when condition is True."""
        (temp_dir / "config.yaml").write_text("key: val\n")
        result = (
            RawConfigBuilder()
            .from_directory(temp_dir, when=lambda: True)
            .build_dict()
        )
        assert "config" in result
