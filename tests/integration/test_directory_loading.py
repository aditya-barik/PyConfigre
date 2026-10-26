"""
Use case: directory-based multi-file configuration loading.

Applications often split configuration across multiple files in a directory
(e.g. ``config/database.yaml``, ``config/server.yaml``).  These tests verify
the standalone ``load_directory()`` function, the ``ConfigNamespace`` wrapper,
and the builder's ``from_directory()`` method in realistic scenarios.
"""

import pytest

from pyconfigre import (
    ConfigNamespace,
    RawConfigBuilder,
    load_directory,
)
from pyconfigre.exceptions import ConfigLoadError, ConfigNotFoundError


@pytest.mark.integration
class TestLoadDirectory:
    """Standalone load_directory() in realistic scenarios."""

    def test_load_multiple_yaml_files(self, cfg_dir):
        """Each YAML file in the directory becomes a namespace key."""
        (cfg_dir / "server.yaml").write_text("host: 0.0.0.0\nport: 8080\n")
        (cfg_dir / "database.yaml").write_text("host: db.local\nport: 5432\n")

        ns = load_directory(cfg_dir)

        assert isinstance(ns, ConfigNamespace)
        assert ns.server["host"] == "0.0.0.0"
        assert ns.server["port"] == 8080
        assert ns.database["host"] == "db.local"
        assert ns.database["port"] == 5432

    def test_mixed_formats_in_directory(self, cfg_dir):
        """YAML, JSON, and TOML files coexist in one directory."""
        (cfg_dir / "server.yaml").write_text("host: 0.0.0.0\nport: 8080\n")
        (cfg_dir / "database.json").write_text('{"host": "db.local", "port": 5432}')
        (cfg_dir / "cache.toml").write_text(
            'host = "redis.local"\nport = 6379\n'
        )

        ns = load_directory(cfg_dir)

        assert ns.server["host"] == "0.0.0.0"
        assert ns.database["host"] == "db.local"
        assert ns.cache["host"] == "redis.local"

    def test_namespace_attribute_and_dict_access(self, cfg_dir):
        """ConfigNamespace supports both attribute and bracket access."""
        (cfg_dir / "app.yaml").write_text("name: myapp\nversion: 1.0\n")

        ns = load_directory(cfg_dir)

        assert ns.app["name"] == ns["app"]["name"]
        assert ns.app["name"] == "myapp"

    def test_namespace_contains_check(self, cfg_dir):
        """The ``in`` operator works on ConfigNamespace keys."""
        (cfg_dir / "server.yaml").write_text("port: 8080\n")

        ns = load_directory(cfg_dir)

        assert "server" in ns
        assert "missing" not in ns

    def test_namespace_is_read_only(self, cfg_dir):
        """ConfigNamespace rejects attribute assignment."""
        (cfg_dir / "app.yaml").write_text("name: myapp\n")

        ns = load_directory(cfg_dir)

        with pytest.raises(AttributeError, match="read-only"):
            ns.app = {"name": "hacked"}

    def test_hidden_files_skipped_by_default(self, cfg_dir):
        """Files starting with '.' are skipped by default."""
        (cfg_dir / "server.yaml").write_text("port: 8080\n")
        (cfg_dir / ".secrets.yaml").write_text("api_key: hidden\n")

        ns = load_directory(cfg_dir)

        assert "server" in ns
        assert ".secrets" not in ns
        assert "secrets" not in ns

    def test_unsupported_extensions_skipped_by_default(self, cfg_dir):
        """Files with unsupported extensions are silently skipped."""
        (cfg_dir / "server.yaml").write_text("port: 8080\n")
        (cfg_dir / "notes.txt").write_text("This is not config.\n")
        (cfg_dir / "README.md").write_text("# Config directory\n")

        ns = load_directory(cfg_dir)

        assert "server" in ns
        assert "notes" not in ns
        assert "README" not in ns

    def test_unsupported_extensions_raise_mode(self, cfg_dir):
        """unknown_extensions='raise' raises ValueError on unsupported files."""
        (cfg_dir / "server.yaml").write_text("port: 8080\n")
        (cfg_dir / "notes.txt").write_text("not config\n")

        with pytest.raises(ValueError, match="Unsupported"):
            load_directory(cfg_dir, unknown_extensions="raise")

    def test_nonexistent_directory_raises(self):
        """Loading from a nonexistent directory raises ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError, match="not found"):
            load_directory("/nonexistent/path/config")

    def test_file_path_raises(self, cfg_dir):
        """Loading from a file (not a directory) raises ConfigLoadError."""
        f = cfg_dir / "single.yaml"
        f.write_text("key: value\n")

        with pytest.raises(ConfigLoadError, match="Not a directory"):
            load_directory(f)


@pytest.mark.integration
class TestFromDirectory:
    """Builder's from_directory() in realistic pipelines."""

    def test_directory_merged_into_pipeline(self, cfg_dir):
        """from_directory() merges directory files into the builder pipeline."""
        conf_dir = cfg_dir / "config"
        conf_dir.mkdir()
        (conf_dir / "server.yaml").write_text(
            "host: 0.0.0.0\nport: 8080\nworkers: 4\ndebug: false\n"
        )
        (conf_dir / "database.yaml").write_text(
            "host: db.local\nport: 5432\nname: appdb\n"
            "username: admin\npassword: secret\n"
        )

        result = RawConfigBuilder().from_directory(conf_dir).build_dict()

        assert result["server"]["host"] == "0.0.0.0"
        assert result["server"]["port"] == 8080
        assert result["database"]["host"] == "db.local"
        assert result["database"]["name"] == "appdb"

    def test_directory_then_env_override(self, cfg_dir):
        """Pattern: load directory defaults, then override with env vars.

        A typical deployment pattern: config directory provides defaults,
        environment variables override specific values in production.
        """
        from .conftest import env_vars

        conf_dir = cfg_dir / "config"
        conf_dir.mkdir()
        (conf_dir / "server.yaml").write_text(
            "host: 0.0.0.0\nport: 8080\nworkers: 4\ndebug: false\n"
        )
        (conf_dir / "database.yaml").write_text(
            "host: localhost\nport: 5432\nname: appdb\n"
            "username: dev\npassword: devpass\n"
        )

        with env_vars(
            APP__DATABASE__HOST="prod-db.example.com",
            APP__DATABASE__PASSWORD="prod-secret",
        ):
            result = (
                RawConfigBuilder()
                .from_directory(conf_dir)
                .from_env("APP__")
                .build_dict()
            )

        assert result["database"]["host"] == "prod-db.example.com"
        assert result["database"]["password"] == "prod-secret"
        assert result["database"]["username"] == "dev"
        assert result["server"]["port"] == 8080

    def test_directory_combined_with_file(self, cfg_dir):
        """Pattern: single base file + directory of component configs."""
        base = cfg_dir / "base.yaml"
        base.write_text("app_name: myapp\nversion: 1.0.0\n")

        components = cfg_dir / "components"
        components.mkdir()
        (components / "server.yaml").write_text(
            "host: 0.0.0.0\nport: 8080\nworkers: 4\ndebug: false\n"
        )
        (components / "database.yaml").write_text(
            "host: localhost\nport: 5432\nname: mydb\n"
            "username: admin\npassword: pass\n"
        )

        result = (
            RawConfigBuilder()
            .from_file(base)
            .from_directory(components)
            .build_dict()
        )

        assert result["app_name"] == "myapp"
        assert result["server"]["host"] == "0.0.0.0"
        assert result["database"]["name"] == "mydb"

    def test_from_directory_with_when_false(self, cfg_dir):
        """from_directory with when=False skips the entire directory."""
        conf_dir = cfg_dir / "config"
        conf_dir.mkdir()
        (conf_dir / "server.yaml").write_text("port: 9999\n")

        result = (
            RawConfigBuilder()
            .from_dict({"port": 8000})
            .from_directory(conf_dir, when=lambda: False)
            .build_dict()
        )

        assert result["port"] == 8000

    def test_empty_directory_produces_empty_namespace(self, cfg_dir):
        """An empty directory produces no keys."""
        empty = cfg_dir / "empty"
        empty.mkdir()

        result = RawConfigBuilder().from_directory(empty).build_dict()

        assert result == {}
