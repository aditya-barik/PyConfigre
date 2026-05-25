"""
Use case: loading configuration from environment variables.

Covers flat keys, double-underscore nesting, prefix stripping, case
handling, all value types, and the integer-before-float parse order fix
from v0.1.1.
"""

import os
from contextlib import contextmanager

import pytest

from pyconfigre import ConfigBuilder

from .conftest import AppConfig, SimpleConfig

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


@contextmanager
def _env(**kwargs):
    """Set env vars for the duration of a with-block, then clean up."""
    for k, v in kwargs.items():
        os.environ[k] = v
    try:
        yield
    finally:
        for k in kwargs:
            os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestENVLoading:
    """Load configuration from environment variables."""

    def test_flat_env_vars_with_prefix(self):
        """Prefixed env vars produce a flat config after prefix is stripped."""
        with _env(
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
        with _env(
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
        with _env(PYCFG_CANARY_NAME="canary-value"):
            # Must be called inside the with block — the env var is only
            # set for the duration of the context manager.
            builder = ConfigBuilder(SimpleConfig).from_env()
            raw = builder.peek()

        assert "pycfg_canary_name" in raw
        assert raw["pycfg_canary_name"] == "canary-value"

    def test_strip_prefix_false_keeps_prefix_in_key(self):
        """strip_prefix=False retains the prefix as part of the key name."""
        with _env(MYAPP_NAME="prefixed-app"):
            builder = ConfigBuilder(SimpleConfig).from_env("MYAPP_", strip_prefix=False)
            raw = builder.peek()

        assert "myapp_name" in raw
        assert raw["myapp_name"] == "prefixed-app"

    def test_lowercase_false_preserves_original_case(self):
        """lowercase=False keeps the original uppercase env var names."""
        with _env(UPPER_NAME="case-test"):
            builder = ConfigBuilder(SimpleConfig).from_env("UPPER_", lowercase=False)
            raw = builder.peek()

        assert "NAME" in raw
        assert raw["NAME"] == "case-test"

    def test_nested_false_keeps_double_underscore_flat(self):
        """nested=False prevents __ from being treated as a separator."""
        with _env(FLAT__DB__HOST="some-host"):
            builder = ConfigBuilder(SimpleConfig).from_env("FLAT__", nested=False)
            raw = builder.peek()

        # Key preserved with __ intact, no nesting
        assert "db__host" in raw
        assert raw["db__host"] == "some-host"

    def test_all_value_types_parsed(self):
        """Env var string values are coerced to their correct Python types."""
        with _env(
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
        with _env(INT_PORT="8000"):
            builder = ConfigBuilder(SimpleConfig).from_env("INT_")
            raw = builder.peek()

        assert raw["port"] == 8000
        assert isinstance(raw["port"], int), (
            f"Expected int but got {type(raw['port']).__name__}. "
            "Check that int() is attempted before float() in _parse_value."
        )
