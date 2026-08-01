"""
Use case: schema validation and type enforcement through the builders.

PyConfigre's value proposition over raw file parsing is type-safe, validated
configuration. These tests verify that validation fires correctly — both for
success paths and for the specific errors users will encounter in practice.

Covers Pydantic validation (ConfigBuilder) and dataclass instantiation /
coercion (DataClassConfigBuilder).
"""

import warnings

import pytest

from pyconfigre import ConfigBuilder, DataClassConfigBuilder
from pyconfigre.exceptions import ConfigValidationError

from .conftest import (
    AppConfig,
    ComplexConfigDC,
    DatabaseConfig,
    DatabaseConfigDC,
    ServerConfig,
    SimpleConfig,
    SimpleConfigDC,
)


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


@pytest.mark.integration
class TestDataClassValidation:
    """DataClassConfigBuilder validation, coercion, and unknown_fields modes."""

    def test_empty_config_uses_defaults(self):
        """A DataClassConfigBuilder with no sources uses field defaults."""
        config = DataClassConfigBuilder(SimpleConfigDC).build()

        assert config.name == "default"
        assert config.debug is False
        assert config.port == 8000
        assert config.api_key is None

    def test_string_values_coerced_from_dict(self):
        """String values in from_dict() are coerced to int/float/bool."""
        from dataclasses import dataclass

        @dataclass
        class AllTypesConfigDC:
            name: str
            count: int
            ratio: float
            active: bool

        config = (
            DataClassConfigBuilder(AllTypesConfigDC, unknown_fields="ignore")
            .from_dict(
                {
                    "name": "coerced",
                    "count": "42",
                    "ratio": "3.14",
                    "active": "yes",
                }
            )
            .build()
        )

        assert config.name == "coerced"
        assert config.count == 42
        assert config.ratio == 3.14
        assert config.active is True

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
