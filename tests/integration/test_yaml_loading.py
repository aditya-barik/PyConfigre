"""
Use case: loading configuration from YAML files.

Covers flat configs, nested sections, all primitive types, both .yaml and
.yml extensions, empty files, and parse error handling.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.exceptions import ConfigLoadError

from .conftest import AllTypesConfig, AppConfig, SimpleConfig


@pytest.mark.integration
class TestYAMLLoading:
    """Load configuration from YAML files."""

    def test_flat_yaml(self, cfg_dir):
        """A flat YAML file produces a validated config with all values set."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: my-service\ndebug: true\nport: 9000\napi_key: tok-abc123\n")

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert config.name == "my-service"
        assert config.debug is True
        assert config.port == 9000
        assert config.api_key == "tok-abc123"

    def test_nested_yaml(self, cfg_dir):
        """A YAML file with nested sections maps to nested Pydantic models."""
        f = cfg_dir / "app.yaml"
        f.write_text(
            "app_name: payments-service\n"
            "version: 2.0.0\n"
            "\n"
            "server:\n"
            "  host: 0.0.0.0\n"
            "  port: 8080\n"
            "  workers: 8\n"
            "  debug: false\n"
            "\n"
            "database:\n"
            "  host: db.prod.example.com\n"
            "  port: 5432\n"
            "  name: payments\n"
            "  username: svc_user\n"
            "  password: hunter2\n"
            "\n"
            "cache:\n"
            "  host: redis.prod.example.com\n"
            "  port: 6380\n"
            "  ttl_seconds: 300\n"
            "  enabled: true\n"
        )

        config = ConfigBuilder(AppConfig).from_file(f).build()

        assert config.app_name == "payments-service"
        assert config.version == "2.0.0"

        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8080
        assert config.server.workers == 8
        assert config.server.debug is False

        assert config.database.host == "db.prod.example.com"
        assert config.database.port == 5432
        assert config.database.name == "payments"

        assert config.cache.host == "redis.prod.example.com"
        assert config.cache.ttl_seconds == 300
        assert config.cache.enabled is True

    def test_all_primitive_types(self, cfg_dir):
        """YAML correctly parses string, int, float, bool, list, dict, and null."""
        f = cfg_dir / "types.yaml"
        f.write_text(
            "name: type-test\n"
            "count: 42\n"
            "ratio: 0.75\n"
            "active: true\n"
            "nullable: null\n"
            "tags:\n"
            "  - alpha\n"
            "  - beta\n"
            "  - gamma\n"
            "metadata:\n"
            "  region: us-east-1\n"
            "  tier: premium\n"
        )

        config = ConfigBuilder(AllTypesConfig).from_file(f).build()

        assert config.name == "type-test"
        assert config.count == 42
        assert isinstance(config.count, int)
        assert config.ratio == 0.75
        assert isinstance(config.ratio, float)
        assert config.active is True
        assert isinstance(config.active, bool)
        assert config.nullable is None
        assert config.tags == ["alpha", "beta", "gamma"]
        assert config.metadata["region"] == "us-east-1"
        assert config.metadata["tier"] == "premium"

    def test_empty_yaml_uses_defaults(self, cfg_dir):
        """An empty YAML file is valid — all schema defaults are used."""
        f = cfg_dir / "empty.yaml"
        f.write_text("")

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert config.name == "default"
        assert config.debug is False
        assert config.port == 8000
        assert config.api_key is None

    def test_yml_extension(self, cfg_dir):
        """Files with .yml extension are auto-detected as YAML."""
        f = cfg_dir / "config.yml"
        f.write_text("name: from-yml\nport: 7777\n")

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert config.name == "from-yml"
        assert config.port == 7777

    def test_yaml_parse_error(self, cfg_dir):
        """A YAML file with invalid syntax raises ConfigLoadError."""
        f = cfg_dir / "broken.yaml"
        f.write_text("key: valid\nbad: :\n  - orphan: [unclosed\n")

        with pytest.raises(ConfigLoadError, match="Failed to parse YAML"):
            ConfigBuilder(SimpleConfig).from_file(f).build()
