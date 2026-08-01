"""
Use case: loading configuration from environment variables.

Covers flat keys, double-underscore nesting, prefix stripping, case
handling, all value types, and the integer-before-float parse order fix
from v0.1.1.
"""

import pytest

from pyconfigre import ConfigBuilder, DataClassConfigBuilder

from .conftest import AppConfig, SimpleConfig, SimpleConfigDC, env_vars


@pytest.mark.integration
class TestENVLoading:
    """Load configuration from environment variables."""

    def test_flat_env_vars_with_prefix(self):
        """Prefixed env vars produce a flat config after prefix is stripped."""
        with env_vars(
            SVC_NAME="env-service",
            SVC_DEBUG="false",
            SVC_PORT="7070",
            SVC_API_KEY="env-key-abc",
        ):
            config = ConfigBuilder(SimpleConfig).from_env("SVC_").build()

        assert config.name == "env-service"
        assert config.debug is False
        assert config.port == 7070
        assert config.api_key == "env-key-abc"

    def test_double_underscore_nesting(self):
        """Double-underscore separators expand into nested Pydantic models.

        This is the core fix for Issue-3 in v0.1.1. MYAPP__SERVER__PORT
        must produce config.server.port, not config["server__port"].
        """
        with env_vars(
            APP__APP_NAME="nested-service",
            APP__SERVER__HOST="10.0.0.1",
            APP__SERVER__PORT="9090",
            APP__SERVER__WORKERS="8",
            APP__SERVER__DEBUG="false",
            APP__DATABASE__HOST="db.internal",
            APP__DATABASE__PORT="5432",
            APP__DATABASE__NAME="prod",
            APP__DATABASE__USERNAME="svc",
            APP__DATABASE__PASSWORD="secret",
        ):
            config = ConfigBuilder(AppConfig).from_env("APP__").build()

        assert config.app_name == "nested-service"
        assert config.server.host == "10.0.0.1"
        assert config.server.port == 9090
        assert config.server.workers == 8
        assert config.server.debug is False
        assert config.database.host == "db.internal"
        assert config.database.name == "prod"

    def test_no_prefix_loads_all_vars(self):
        """Without a prefix, all environment variables are loaded.

        Uses a uniquely-prefixed canary key to avoid colliding with
        real process environment variables on any machine.
        """
        with env_vars(PYCFG_CANARY_NAME="canary-value"):
            # Must be called inside the with block — the env var is only
            # set for the duration of the context manager.
            builder = ConfigBuilder(SimpleConfig).from_env()
            raw = builder.peek()

        assert "pycfg_canary_name" in raw
        assert raw["pycfg_canary_name"] == "canary-value"

    def test_strip_prefix_false_keeps_prefix_in_key(self):
        """strip_prefix=False retains the prefix as part of the key name."""
        with env_vars(MYAPP_NAME="prefixed-app"):
            builder = ConfigBuilder(SimpleConfig).from_env("MYAPP_", strip_prefix=False)
            raw = builder.peek()

        assert "myapp_name" in raw
        assert raw["myapp_name"] == "prefixed-app"

    def test_lowercase_false_preserves_original_case(self):
        """lowercase=False keeps the original uppercase env var names."""
        with env_vars(UPPER_NAME="case-test"):
            builder = ConfigBuilder(SimpleConfig).from_env("UPPER_", lowercase=False)
            raw = builder.peek()

        assert "NAME" in raw
        assert raw["NAME"] == "case-test"

    def test_nested_false_keeps_double_underscore_flat(self):
        """nested=False prevents __ from being treated as a separator."""
        with env_vars(FLAT__DB__HOST="some-host"):
            builder = ConfigBuilder(SimpleConfig).from_env("FLAT__", nested=False)
            raw = builder.peek()

        # Key preserved with __ intact, no nesting
        assert "db__host" in raw
        assert raw["db__host"] == "some-host"

    def test_all_value_types_parsed(self):
        """Env var string values are coerced to their correct Python types."""
        with env_vars(
            T_NAME="type-test",
            T_DEBUG="true",
            T_PORT="42",
            T_RATIO="3.14",
            T_API_KEY="null",
        ):
            config = ConfigBuilder(SimpleConfig).from_env("T_").build()

        assert config.name == "type-test"
        assert config.debug is True
        assert isinstance(config.debug, bool)
        assert config.port == 42
        assert isinstance(config.port, int)
        assert config.api_key is None

    def test_integer_parses_as_int_not_float(self):
        """Integer env var values must parse as int, not float.

        This is the parse-order fix in v0.1.1: int() is attempted before
        float() so that "8000" → 8000, not 8000.0.
        """
        with env_vars(INT_PORT="8000"):
            builder = ConfigBuilder(SimpleConfig).from_env("INT_")
            raw = builder.peek()

        assert raw["port"] == 8000
        assert isinstance(raw["port"], int), (
            f"Expected int but got {type(raw['port']).__name__}. "
            "Check that int() is attempted before float() in _parse_value."
        )


@pytest.mark.integration
class TestDataClassENVCoercion:
    """DataClassConfigBuilder string coercion from environment variables."""

    def test_env_strings_coerced_to_field_types(self):
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

    def test_falsy_bool_strings_from_env(self):
        """Falsy string values are coerced to False for bool fields."""
        with env_vars(
            DCSVC_NAME="env-service",
            DCSVC_DEBUG="no",
            DCSVC_PORT="7070",
        ):
            config = DataClassConfigBuilder(SimpleConfigDC).from_env("DCSVC_").build()

        assert config.debug is False

    def test_nested_env_vars_instantiate_dataclasses(self):
        """Double-underscore env vars produce nested dataclass instances."""
        from dataclasses import dataclass, field

        @dataclass
        class ServerConfigDC:
            host: str = "0.0.0.0"
            port: int = 8000
            debug: bool = False

        @dataclass
        class DatabaseConfigDC:
            name: str
            username: str
            password: str
            host: str = "localhost"
            port: int = 5432

        @dataclass
        class AppConfigDC:
            database: DatabaseConfigDC
            app_name: str = "myapp"
            version: str = "0.1.0"
            server: ServerConfigDC = field(default_factory=ServerConfigDC)

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
