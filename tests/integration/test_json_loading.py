"""
Use case: loading configuration from JSON files.

Covers flat configs, nested objects, all primitive types, malformed JSON,
and non-object root handling.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.exceptions import ConfigLoadError

from .conftest import AllTypesConfig, AppConfig, SimpleConfig


@pytest.mark.integration
class TestJSONLoading:
    """Load configuration from JSON files."""

    def test_flat_json(self, cfg_dir):
        """A flat JSON object produces a validated config with all values set."""
        f = cfg_dir / "app.json"
        f.write_text(
            "{\n"
            '  "name": "json-service",\n'
            '  "debug": false,\n'
            '  "port": 4000,\n'
            '  "api_key": "json-key-xyz"\n'
            "}\n"
        )

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert config.name == "json-service"
        assert config.debug is False
        assert config.port == 4000
        assert config.api_key == "json-key-xyz"

    def test_nested_json(self, cfg_dir):
        """A JSON file with nested objects maps to nested Pydantic models."""
        f = cfg_dir / "app.json"
        f.write_text(
            "{\n"
            '  "app_name": "billing-service",\n'
            '  "version": "3.1.0",\n'
            '  "server": {\n'
            '    "host": "127.0.0.1",\n'
            '    "port": 9090,\n'
            '    "workers": 2,\n'
            '    "debug": true\n'
            "  },\n"
            '  "database": {\n'
            '    "host": "db.staging.example.com",\n'
            '    "port": 5433,\n'
            '    "name": "billing_staging",\n'
            '    "username": "staging_user",\n'
            '    "password": "staging_pass"\n'
            "  }\n"
            "}\n"
        )

        config = ConfigBuilder(AppConfig).from_file(f).build()

        assert config.app_name == "billing-service"
        assert config.version == "3.1.0"
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 9090
        assert config.server.debug is True
        assert config.database.host == "db.staging.example.com"
        assert config.database.name == "billing_staging"

    def test_all_primitive_types(self, cfg_dir):
        """JSON correctly handles strings, numbers, booleans, arrays, objects, null."""
        f = cfg_dir / "types.json"
        f.write_text(
            "{\n"
            '  "name": "type-test",\n'
            '  "count": 99,\n'
            '  "ratio": 3.14,\n'
            '  "active": true,\n'
            '  "nullable": null,\n'
            '  "tags": ["x", "y", "z"],\n'
            '  "metadata": {"env": "test", "version": 2}\n'
            "}\n"
        )

        config = ConfigBuilder(AllTypesConfig).from_file(f).build()

        assert config.name == "type-test"
        assert config.count == 99
        assert isinstance(config.count, int)
        assert config.ratio == 3.14
        assert isinstance(config.ratio, float)
        assert config.active is True
        assert config.nullable is None
        assert config.tags == ["x", "y", "z"]
        assert config.metadata["env"] == "test"

    def test_malformed_json(self, cfg_dir):
        """A JSON file with invalid syntax raises ConfigLoadError."""
        f = cfg_dir / "broken.json"
        f.write_text('{"key": "value", "bad": }')

        with pytest.raises(ConfigLoadError, match="Failed to parse JSON"):
            ConfigBuilder(SimpleConfig).from_file(f).build()

    def test_json_array_root_raises(self, cfg_dir):
        """A JSON file whose root is an array (not an object) raises ConfigLoadError.

        PyConfigre requires configuration to be a key-value mapping. A root-level
        array has no key names and cannot be mapped to a Pydantic model.
        """
        f = cfg_dir / "array.json"
        f.write_text('["item1", "item2", "item3"]')

        with pytest.raises(ConfigLoadError, match="not a dictionary"):
            ConfigBuilder(SimpleConfig).from_file(f).build()
