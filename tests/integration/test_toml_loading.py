"""
Use case: loading configuration from TOML files.

Covers flat configs, nested tables, all primitive types, and parse error
handling. TOML is the standard configuration format for Python tooling
(pyproject.toml) and is increasingly common for application config.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.exceptions import ConfigLoadError

from .conftest import AllTypesConfig, AppConfig, SimpleConfig


@pytest.mark.integration
class TestTOMLLoading:
    """Load configuration from TOML files."""

    def test_flat_toml(self, cfg_dir):
        """A flat TOML file produces a validated config with all values set."""
        f = cfg_dir / "app.toml"
        f.write_text(
            'name = "toml-service"\n'
            "debug = true\n"
            "port = 5050\n"
            'api_key = "toml-secret"\n'
        )

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert config.name == "toml-service"
        assert config.debug is True
        assert config.port == 5050
        assert config.api_key == "toml-secret"

    def test_nested_toml_tables(self, cfg_dir):
        """A TOML file with nested tables maps to nested Pydantic models."""
        f = cfg_dir / "app.toml"
        f.write_text(
            'app_name = "notifications-service"\n'
            'version = "1.2.3"\n'
            "\n"
            "[server]\n"
            'host = "0.0.0.0"\n'
            "port = 8888\n"
            "workers = 16\n"
            "debug = false\n"
            "\n"
            "[database]\n"
            'host = "db.toml.example.com"\n'
            "port = 5432\n"
            'name = "notifications"\n'
            'username = "notif_user"\n'
            'password = "notif_pass"\n'
            "\n"
            "[cache]\n"
            'host = "cache.toml.example.com"\n'
            "port = 6379\n"
            "ttl_seconds = 600\n"
            "enabled = true\n"
        )

        config = ConfigBuilder(AppConfig).from_file(f).build()

        assert config.app_name == "notifications-service"
        assert config.version == "1.2.3"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8888
        assert config.server.workers == 16
        assert config.database.host == "db.toml.example.com"
        assert config.database.name == "notifications"
        assert config.cache.ttl_seconds == 600

    def test_all_primitive_types(self, cfg_dir):
        """TOML correctly handles string, int, float, bool, array, inline tables."""
        f = cfg_dir / "types.toml"
        f.write_text(
            'name = "toml-types"\n'
            "count = 7\n"
            "ratio = 2.718\n"
            "active = false\n"
            'tags = ["one", "two", "three"]\n'
            "\n"
            "[metadata]\n"
            'region = "eu-west-1"\n'
            "tier = 3\n"
        )

        config = ConfigBuilder(AllTypesConfig).from_file(f).build()

        assert config.name == "toml-types"
        assert config.count == 7
        assert isinstance(config.count, int)
        assert config.ratio == pytest.approx(2.718)
        assert isinstance(config.ratio, float)
        assert config.active is False
        assert config.tags == ["one", "two", "three"]
        assert config.metadata["region"] == "eu-west-1"

    def test_toml_parse_error(self, cfg_dir):
        """A TOML file with invalid syntax raises ConfigLoadError."""
        f = cfg_dir / "broken.toml"
        f.write_text("valid_key = 'ok'\nbad key with spaces = 'invalid'\n")

        with pytest.raises(ConfigLoadError, match="Failed to (parse|load) TOML"):
            ConfigBuilder(SimpleConfig).from_file(f).build()
