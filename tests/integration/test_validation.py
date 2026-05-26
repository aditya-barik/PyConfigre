"""
Use case: Pydantic validation through the builder.

PyConfigre's value proposition over raw file parsing is type-safe, validated
configuration. These tests verify that validation fires correctly — both for
success paths and for the specific errors users will encounter in practice.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.exceptions import ConfigValidationError

from .conftest import AppConfig, DatabaseConfig, ServerConfig, SimpleConfig


@pytest.mark.integration
class TestValidation:
    """Pydantic validation is applied correctly at build() time."""

    def test_valid_config_returns_typed_model(self, cfg_dir):
        """A fully valid config returns a typed Pydantic model instance."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: valid-app\ndebug: true\nport: 8080\n")

        config = ConfigBuilder(SimpleConfig).from_file(f).build()

        assert isinstance(config, SimpleConfig)
        assert config.name == "valid-app"
        assert config.debug is True
        assert config.port == 8080

    def test_missing_required_field_raises(self):
        """Omitting a required field (no default) raises ConfigValidationError."""
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            # DatabaseConfig.name is required — no default
            ConfigBuilder(DatabaseConfig).from_dict(
                {
                    "host": "localhost",
                    "username": "user",
                    "password": "pass",
                    # "name" intentionally omitted
                }
            ).build()

    def test_wrong_type_raises(self):
        """A value with an incompatible type raises ConfigValidationError."""
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            ConfigBuilder(SimpleConfig).from_dict(
                {
                    "name": "test",
                    "port": "not-a-number",  # string where int expected
                }
            ).build()

    def test_field_constraint_violated_raises(self):
        """
        A value that violates a Pydantic Field constraint raises ConfigValidationError.

        ServerConfig.port has ge=1, le=65535. Values outside that range must fail.
        """
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            ConfigBuilder(ServerConfig).from_dict(
                {
                    "port": 99999,  # exceeds le=65535
                }
            ).build()

        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            ConfigBuilder(ServerConfig).from_dict(
                {
                    "port": 0,  # below ge=1
                }
            ).build()

    def test_nested_model_validated_correctly(self, cfg_dir):
        """Nested Pydantic models are validated as part of the parent model."""
        f = cfg_dir / "app.yaml"
        f.write_text(
            "app_name: validated-app\n"
            "database:\n"
            "  host: db.example.com\n"
            "  port: 5432\n"
            "  name: appdb\n"
            "  username: admin\n"
            "  password: secure\n"
        )

        config = ConfigBuilder(AppConfig).from_file(f).build()

        assert isinstance(config.database, DatabaseConfig)
        assert config.database.host == "db.example.com"
        assert config.database.port == 5432

    def test_optional_field_accepts_none(self):
        """An Optional field accepts null / None without raising."""
        config = (
            ConfigBuilder(SimpleConfig)
            .from_dict(
                {
                    "name": "nullable-test",
                    "api_key": None,
                }
            )
            .build()
        )

        assert config.api_key is None

    def test_invalid_type_caught_at_build_not_at_set(self):
        """set() itself does not validate — validation fires only at build().

        This is intentional: the builder is for assembly, not for incremental
        validation. Users set values freely and get a single clear error at
        build() time with full Pydantic context.
        """
        builder = ConfigBuilder(SimpleConfig)

        # set() with a bad type must NOT raise
        builder.set("port", "not-a-number")

        # build() must raise with a clear Pydantic error
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            builder.build()
