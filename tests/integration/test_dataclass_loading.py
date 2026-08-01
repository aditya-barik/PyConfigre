"""Use case: loading configuration into stdlib dataclasses.

Mirrors the ConfigBuilder integration tests but uses DataClassConfigBuilder.
Covers file, env, dict, and multi-source loading plus the dataclass-specific
``unknown_fields`` behaviour and string coercion.
"""

import warnings
from dataclasses import dataclass, field
from typing import Any

import pytest

from pyconfigre import DataClassConfigBuilder
from pyconfigre.exceptions import ConfigValidationError

from .conftest import env_vars


@dataclass
class ServerConfigDC:
    """HTTP server configuration for dataclass integration tests."""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class DatabaseConfigDC:
    """Relational database configuration for dataclass integration tests."""

    name: str
    username: str
    password: str
    host: str = "localhost"
    port: int = 5432


@dataclass
class AppConfigDC:
    """Top-level application config for dataclass integration tests."""

    database: DatabaseConfigDC
    app_name: str = "myapp"
    version: str = "0.1.0"
    server: ServerConfigDC = field(default_factory=ServerConfigDC)


@dataclass
class AllTypesConfigDC:
    """Schema that exercises every primitive type for dataclasses."""

    name: str
    count: int
    ratio: float
    active: bool
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    nullable: str | None = None


@dataclass
class SimpleConfigDC:
    """Minimal schema for dataclass integration tests."""

    name: str = "default"
    debug: bool = False
    port: int = 8000
    api_key: str | None = None


@dataclass
class ComplexConfigDC:
    """Schema with a non-coercible concrete type for pass-through tests."""

    value: complex = 0j


@pytest.mark.integration
class TestDataClassLoading:
    """Load, merge, and validate configuration into stdlib dataclasses."""

    def test_empty_config_uses_defaults(self):
        """A DataClassConfigBuilder with no sources uses field defaults."""
        config = DataClassConfigBuilder(SimpleConfigDC).build()

        assert config.name == "default"
        assert config.debug is False
        assert config.port == 8000
        assert config.api_key is None

    def test_from_yaml_flat(self, cfg_dir):
        """A flat YAML file instantiates a dataclass with the loaded values."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: my-service\ndebug: true\nport: 9000\napi_key: tok-abc123\n")

        config = (
            DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
            .from_file(f)
            .build()
        )

        assert config.name == "my-service"
        assert config.debug is True
        assert config.port == 9000
        assert config.api_key == "tok-abc123"

    def test_from_yaml_nested(self, cfg_dir):
        """A YAML file with nested dicts recursively instantiates dataclasses."""
        f = cfg_dir / "app.yaml"
        f.write_text(
            "app_name: payments-service\n"
            "version: 2.0.0\n"
            "\n"
            "server:\n"
            "  host: 0.0.0.0\n"
            "  port: 8080\n"
            "  debug: false\n"
            "\n"
            "database:\n"
            "  host: db.prod.example.com\n"
            "  port: 5432\n"
            "  name: payments\n"
            "  username: svc_user\n"
            "  password: hunter2\n"
        )

        config = (
            DataClassConfigBuilder(AppConfigDC, unknown_fields="ignore")
            .from_file(f)
            .build()
        )

        assert config.app_name == "payments-service"
        assert config.version == "2.0.0"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8080
        assert config.server.debug is False
        assert config.database.host == "db.prod.example.com"
        assert config.database.name == "payments"

    def test_from_json(self, cfg_dir):
        """A JSON file instantiates a dataclass after auto-detection."""
        f = cfg_dir / "app.json"
        f.write_text(
            "{\n"
            '  "name": "json-service",\n'
            '  "debug": false,\n'
            '  "port": 4000,\n'
            '  "api_key": "json-key-xyz"\n'
            "}\n"
        )

        config = (
            DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
            .from_file(f)
            .build()
        )

        assert config.name == "json-service"
        assert config.debug is False
        assert config.port == 4000
        assert config.api_key == "json-key-xyz"

    def test_from_toml(self, cfg_dir):
        """A TOML file instantiates a dataclass."""
        f = cfg_dir / "app.toml"
        f.write_text(
            'name = "toml-service"\n'
            "debug = true\n"
            "port = 5050\n"
            'api_key = "toml-secret"\n'
        )

        config = (
            DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
            .from_file(f)
            .build()
        )

        assert config.name == "toml-service"
        assert config.debug is True
        assert config.port == 5050
        assert config.api_key == "toml-secret"

    def test_from_env_string_coercion(self):
        """Environment variables are strings; dataclass builder coerces them."""
        with env_vars(
            DCSVC_NAME="env-service",
            DCSVC_DEBUG="true",
            DCSVC_PORT="7070",
            DCSVC_API_KEY="env-key-abc",
        ):
            config = DataClassConfigBuilder(SimpleConfigDC).from_env("DCSVC_").build()

        assert config.name == "env-service"
        assert config.debug is True
        assert isinstance(config.debug, bool)
        assert config.port == 7070
        assert isinstance(config.port, int)
        assert config.api_key == "env-key-abc"

    def test_from_env_nested(self):
        """Double-underscore env vars produce nested dataclass instances."""
        with env_vars(
            DCAPP__APP_NAME="nested-service",
            DCAPP__SERVER__HOST="10.0.0.1",
            DCAPP__SERVER__PORT="9090",
            DCAPP__SERVER__DEBUG="false",
            DCAPP__DATABASE__HOST="db.internal",
            DCAPP__DATABASE__PORT="5432",
            DCAPP__DATABASE__NAME="prod",
            DCAPP__DATABASE__USERNAME="svc",
            DCAPP__DATABASE__PASSWORD="secret",
        ):
            config = DataClassConfigBuilder(AppConfigDC).from_env("DCAPP__").build()

        assert config.app_name == "nested-service"
        assert config.server.host == "10.0.0.1"
        assert config.server.port == 9090
        assert config.server.debug is False
        assert config.database.host == "db.internal"
        assert config.database.name == "prod"

    def test_all_primitive_types_from_yaml(self, cfg_dir):
        """YAML with all primitive types maps to a dataclass."""
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

        config = (
            DataClassConfigBuilder(AllTypesConfigDC, unknown_fields="ignore")
            .from_file(f)
            .build()
        )

        assert config.name == "type-test"
        assert config.count == 42
        assert isinstance(config.count, int)
        assert config.ratio == 0.75
        assert isinstance(config.ratio, float)
        assert config.active is True
        assert config.nullable is None
        assert config.tags == ["alpha", "beta", "gamma"]
        assert config.metadata["region"] == "us-east-1"

    def test_string_values_coerced_from_dict(self):
        """String values in from_dict() are coerced to int/float/bool."""
        config = (
            DataClassConfigBuilder(AllTypesConfigDC, unknown_fields="ignore")
            .from_dict(
                {
                    "name": "coerced",
                    "count": "42",
                    "ratio": "3.14",
                    "active": "yes",
                    "tags": ["x", "y"],
                }
            )
            .build()
        )

        assert config.name == "coerced"
        assert config.count == 42
        assert config.ratio == 3.14
        assert config.active is True

    def test_falsy_bool_strings_from_env(self):
        """Falsy string values are coerced to False for bool fields."""
        with env_vars(
            DCSVC_NAME="env-service",
            DCSVC_DEBUG="no",
            DCSVC_PORT="7070",
        ):
            config = DataClassConfigBuilder(SimpleConfigDC).from_env("DCSVC_").build()

        assert config.debug is False

    def test_invalid_bool_string_raises(self):
        """An unrecognised bool string raises ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Cannot coerce"):
            (
                DataClassConfigBuilder(SimpleConfigDC)
                .from_dict({"name": "bad", "debug": "maybe"})
                .build()
            )

    def test_bool_value_for_int_field_is_coerced_to_int(self):
        """bool is a subclass of int; True/False for an int field becomes 1/0."""
        config = (
            DataClassConfigBuilder(SimpleConfigDC).from_dict({"port": True}).build()
        )

        assert config.port == 1
        assert isinstance(config.port, int)
        assert not isinstance(config.port, bool)

    def test_falsy_bool_string_from_dict(self):
        """Falsy string values (e.g. 'no') are coerced to False for bool fields."""
        config = (
            DataClassConfigBuilder(SimpleConfigDC)
            .from_dict({"name": "falsy", "debug": "no"})
            .build()
        )

        assert config.debug is False

    def test_unrecognised_type_string_passes_through(self):
        """String values for non-coercible concrete types are passed through."""
        config = (
            DataClassConfigBuilder(ComplexConfigDC).from_dict({"value": "1+2j"}).build()
        )

        assert config.value == "1+2j"

    def test_multi_source_priority(self, cfg_dir):
        """file < env < dict priority holds for dataclass configs."""
        f = cfg_dir / "base.yaml"
        f.write_text("name: from-file\ndebug: false\nport: 8000\n")

        with env_vars(DC_NAME="from-env", DC_DEBUG="true"):
            config = (
                DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
                .from_file(f)  # name=from-file, debug=false, port=8000
                .from_env("DC_")  # name=from-env, debug=true
                .from_dict({"port": 3000})  # port=3000
                .build()
            )

        assert config.name == "from-env"
        assert config.debug is True
        assert config.port == 3000

    def test_missing_required_field_raises(self):
        """A required dataclass field missing from data raises ConfigValidationError."""
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            # DatabaseConfigDC.name is required — no default
            DataClassConfigBuilder(DatabaseConfigDC).from_dict(
                {
                    "host": "localhost",
                    "username": "user",
                    "password": "pass",
                    # "name" intentionally omitted
                }
            ).build()

    def test_non_dataclass_schema_raises(self):
        """DataClassConfigBuilder requires a @dataclass-decorated class."""

        class NotADataclass:
            pass

        with pytest.raises(TypeError, match="requires a @dataclass class"):
            DataClassConfigBuilder(NotADataclass)  # type: ignore[type-var]

    def test_invalid_unknown_fields_value_raises(self):
        """An unsupported unknown_fields value raises ValueError."""
        with pytest.raises(ValueError, match="unknown_fields must be one of"):
            DataClassConfigBuilder(SimpleConfigDC, unknown_fields="invalid")  # type: ignore[arg-type]

    def test_unknown_fields_warn_by_default(self):
        """Extra dict keys emit a UserWarning unless unknown_fields is changed."""
        with pytest.warns(UserWarning, match="Unknown fields for SimpleConfigDC"):
            config = (
                DataClassConfigBuilder(SimpleConfigDC)
                .from_dict(
                    {
                        "name": "extra",
                        "debug": True,
                        "port": 9000,
                        "unknown_field": "ignored",
                    }
                )
                .build()
            )

        assert config.name == "extra"
        assert not hasattr(config, "unknown_field")

    def test_unknown_fields_ignore_mode(self):
        """unknown_fields='ignore' silently drops extra keys."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            config = (
                DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
                .from_dict(
                    {"name": "ignore", "debug": True, "port": 9000, "extra_key": 123}
                )
                .build()
            )

        assert config.name == "ignore"
        assert not hasattr(config, "extra_key")

    def test_unknown_fields_forbid_mode(self):
        """unknown_fields='forbid' raises ConfigValidationError for extra keys."""
        with pytest.raises(
            ConfigValidationError, match="Unknown fields for SimpleConfigDC"
        ):
            (
                DataClassConfigBuilder(SimpleConfigDC, unknown_fields="forbid")
                .from_dict(
                    {"name": "forbid", "debug": True, "port": 9000, "extra_key": 123}
                )
                .build()
            )
