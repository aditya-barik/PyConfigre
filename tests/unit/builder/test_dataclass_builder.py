"""Test suite for pyconfigre.builder.dataclass_builder — DataClassConfigBuilder.

This module contains unit tests for DataClassConfigBuilder covering basic
instantiation, nested dataclasses, type coercion, error handling,
fluent API, and inheritance from RawConfigBuilder.
"""

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from pyconfigre import DataClassConfigBuilder, RawConfigBuilder
from pyconfigre.builder.dataclass_builder import _coerce_value
from pyconfigre.exceptions import ConfigValidationError

# —— Test dataclass schemas ————————————————————————————————————————————


@dataclass
class FlatConfig:
    """Flat dataclass with defaults for basic tests."""

    app_name: str = "my_app"
    debug: bool = False
    port: int = 8080


@dataclass
class DatabaseConfig:
    """Nested dataclass for database configuration."""

    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"


@dataclass
class NestedConfig:
    """Top-level dataclass with a nested dataclass field."""

    app_name: str = "my_app"
    debug: bool = False
    port: int = 8080
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


@dataclass
class RequiredFieldConfig:
    """Dataclass with a required field (no default)."""

    app_name: str
    port: int = 8080


# —— Basic Instantiation Tests ————————————————————————————————————————


class TestDataClassConfigBuilderBasic:
    """Tests for basic DataClassConfigBuilder instantiation."""

    def test_build_basic_dataclass(self) -> None:
        """Test building a flat dataclass with all defaults.

        Verifies that a fresh DataClassConfigBuilder with no sources
        produces a dataclass instance with all default values.
        """
        config = DataClassConfigBuilder(FlatConfig).build()

        assert isinstance(config, FlatConfig)
        assert config.app_name == "my_app"
        assert config.debug is False
        assert config.port == 8080

    def test_build_basic_dataclass_with_overrides(self) -> None:
        """Test building a flat dataclass with dict overrides."""
        config = (
            DataClassConfigBuilder(FlatConfig)
            .from_dict({"app_name": "overridden", "debug": True, "port": 9000})
            .build()
        )

        assert config.app_name == "overridden"
        assert config.debug is True
        assert config.port == 9000

    def test_build_nested_dataclass(self) -> None:
        """Test recursive nested dataclass instantiation.

        Verifies that a dict containing a nested dict is recursively
        instantiated into the correct nested dataclass.
        """
        config = (
            DataClassConfigBuilder(NestedConfig)
            .from_dict(
                {
                    "app_name": "nested_app",
                    "debug": True,
                    "database": {
                        "host": "db.example.com",
                        "port": 3306,
                        "name": "prod",
                    },
                }
            )
            .build()
        )

        assert isinstance(config, NestedConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert config.app_name == "nested_app"
        assert config.debug is True
        assert config.database.host == "db.example.com"
        assert config.database.port == 3306
        assert config.database.name == "prod"

    def test_build_nested_dataclass_partial_override(self) -> None:
        """Test that partial nested dict uses defaults for missing fields."""
        config = (
            DataClassConfigBuilder(NestedConfig)
            .from_dict({"database": {"host": "remote.host"}})
            .build()
        )

        assert config.database.host == "remote.host"
        assert config.database.port == 5432  # default
        assert config.database.name == "mydb"  # default


# —— File & Env Source Tests ————————————————————————————————————————


class TestDataClassConfigBuilderSources:
    """Tests for DataClassConfigBuilder with file and env sources."""

    def test_build_with_file_source(self, yaml_config_file: Path) -> None:
        """Test building a dataclass from a YAML file source.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config = (
            DataClassConfigBuilder(FlatConfig, unknown_fields="ignore")
            .from_file(yaml_config_file)
            .build()
        )

        assert config.app_name == "test_application_yaml"
        assert config.debug is True
        assert config.port == 9000

    def test_build_with_json_source(self, json_config_file: Path) -> None:
        """Test building a dataclass from a JSON file source.

        Parameters
        ----------
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        config = (
            DataClassConfigBuilder(FlatConfig, unknown_fields="ignore")
            .from_file(json_config_file)
            .build()
        )

        assert config.app_name == "test_application_json"
        assert config.debug is True

    def test_build_with_env_source(self) -> None:
        """Test building a dataclass from environment variables.

        Sets environment variables and verifies they are loaded,
        type-coerced, and properly instantiated into the dataclass.
        """
        os.environ["DCTEST_APP_NAME"] = "env_app"
        os.environ["DCTEST_DEBUG"] = "true"
        os.environ["DCTEST_PORT"] = "3000"

        try:
            config = (
                DataClassConfigBuilder(FlatConfig).from_env(prefix="DCTEST_").build()
            )

            assert config.app_name == "env_app"
            assert config.debug is True
            assert config.port == 3000
        finally:
            for key in ["DCTEST_APP_NAME", "DCTEST_DEBUG", "DCTEST_PORT"]:
                del os.environ[key]

    def test_build_with_multiple_sources_priority(self, yaml_config_file: Path) -> None:
        """Test priority merging with multiple sources → dataclass.

        Later sources override earlier ones: file → dict → set.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config = (
            DataClassConfigBuilder(FlatConfig, unknown_fields="ignore")
            .from_file(yaml_config_file)
            .from_dict({"port": 7000})
            .set("app_name", "priority_app")
            .build()
        )

        assert config.app_name == "priority_app"  # set() wins
        assert config.debug is True  # from YAML
        assert config.port == 7000  # from dict


# —— Type Coercion Tests ————————————————————————————————————————


class TestDataClassConfigBuilderTypeCoercion:
    """Tests for type coercion in DataClassConfigBuilder."""

    def test_type_coercion_str_to_int(self) -> None:
        """Test that string "8080" is coerced to int 8080."""
        config = DataClassConfigBuilder(FlatConfig).from_dict({"port": "8080"}).build()

        assert config.port == 8080
        assert isinstance(config.port, int)

    def test_type_coercion_str_to_float(self) -> None:
        """Test that string "3.14" is coerced to float 3.14."""

        @dataclass
        class FloatConfig:
            rate: float = 1.0

        config = DataClassConfigBuilder(FloatConfig).from_dict({"rate": "3.14"}).build()

        assert config.rate == 3.14
        assert isinstance(config.rate, float)

    def test_type_coercion_str_to_bool_true(self) -> None:
        """Test that truthy strings are coerced to True."""
        for truthy in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
            config = (
                DataClassConfigBuilder(FlatConfig).from_dict({"debug": truthy}).build()
            )
            assert config.debug is True, f"Failed for {truthy!r}"

    def test_type_coercion_str_to_bool_false(self) -> None:
        """Test that falsy strings are coerced to False."""
        for falsy in ["false", "False", "FALSE", "0", "no", "No", "NO"]:
            config = (
                DataClassConfigBuilder(FlatConfig).from_dict({"debug": falsy}).build()
            )
            assert config.debug is False, f"Failed for {falsy!r}"

    def test_type_coercion_invalid_bool_raises(self) -> None:
        """Test that an unrecognised bool string raises ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Cannot coerce"):
            (DataClassConfigBuilder(FlatConfig).from_dict({"debug": "maybe"}).build())

    def test_type_coercion_invalid_int_raises(self) -> None:
        """Test that a non-numeric string for an int field raises error."""
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            (
                DataClassConfigBuilder(FlatConfig)
                .from_dict({"port": "not_a_number"})
                .build()
            )

    def test_bool_value_not_coerced_to_int(self) -> None:
        """Test that a bool True is coerced to int 1 for int fields.

        bool is a subclass of int in Python, so True passed to an int
        field should be coerced to int(True) = 1.
        """
        config = DataClassConfigBuilder(FlatConfig).from_dict({"port": True}).build()

        assert config.port == 1
        assert isinstance(config.port, int)
        assert not isinstance(config.port, bool)

    def test_str_value_passthrough_for_unrecognised_type(self) -> None:
        """Test that string values are passed through for non-coerced types.

        `_coerce_value` only handles int/float/bool. For any other
        target type a string should be returned unchanged so the dataclass
        constructor can attempt its own conversion.
        """
        assert _coerce_value("1+2j", complex) == "1+2j"


# —— Error Handling Tests ————————————————————————————————————————


class TestDataClassConfigBuilderErrors:
    """Tests for error handling in DataClassConfigBuilder."""

    def test_missing_required_field_raises(self) -> None:
        """Test that a missing required field (no default) raises error.

        RequiredFieldConfig has app_name without a default. Building
        without providing it must raise ConfigValidationError.
        """
        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            DataClassConfigBuilder(RequiredFieldConfig).build()

    def test_extra_fields_warn_by_default(self) -> None:
        """Test that extra dict keys emit a UserWarning by default."""
        with pytest.warns(UserWarning, match="Unknown fields for FlatConfig"):
            config = (
                DataClassConfigBuilder(FlatConfig)
                .from_dict(
                    {
                        "app_name": "extra_app",
                        "debug": True,
                        "port": 9000,
                        "unknown_field": "should_be_ignored",
                        "another_extra": 42,
                    }
                )
                .build()
            )

        assert config.app_name == "extra_app"
        assert config.debug is True
        assert config.port == 9000
        assert not hasattr(config, "unknown_field")
        assert not hasattr(config, "another_extra")

    def test_extra_fields_ignore_mode(self) -> None:
        """Test that unknown_fields='ignore' silently drops extra keys."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            config = (
                DataClassConfigBuilder(FlatConfig, unknown_fields="ignore")
                .from_dict(
                    {
                        "app_name": "extra_app",
                        "debug": True,
                        "port": 9000,
                        "unknown_field": "should_be_ignored",
                    }
                )
                .build()
            )

        assert config.app_name == "extra_app"
        assert config.debug is True
        assert config.port == 9000
        assert not hasattr(config, "unknown_field")

    def test_extra_fields_forbid_mode(self) -> None:
        """Test that unknown_fields='forbid' raises ConfigValidationError."""
        with pytest.raises(
            ConfigValidationError, match="Unknown fields for FlatConfig"
        ):
            (
                DataClassConfigBuilder(FlatConfig, unknown_fields="forbid")
                .from_dict(
                    {
                        "app_name": "extra_app",
                        "debug": True,
                        "port": 9000,
                        "unknown_field": "should_fail",
                    }
                )
                .build()
            )

    def test_extra_fields_warn_nested(self) -> None:
        """Test that extra keys in nested dataclasses also warn by default."""
        with pytest.warns(UserWarning, match="Unknown fields for DatabaseConfig"):
            config = (
                DataClassConfigBuilder(NestedConfig)
                .from_dict(
                    {
                        "app_name": "nested_app",
                        "database": {
                            "host": "db.example.com",
                            "unknown_db_field": "ignored",
                        },
                    }
                )
                .build()
            )

        assert config.database.host == "db.example.com"

    def test_non_dataclass_raises(self) -> None:
        """Test that passing a non-dataclass type raises TypeError."""

        class NotADataclass:
            pass

        with pytest.raises(TypeError, match="requires a @dataclass class"):
            DataClassConfigBuilder(NotADataclass)

    def test_non_dataclass_dict_raises(self) -> None:
        """Test that passing dict as schema raises TypeError."""
        with pytest.raises(TypeError, match="requires a @dataclass class"):
            DataClassConfigBuilder(dict)  # type: ignore[type-var]

    def test_invalid_unknown_fields_raises(self) -> None:
        """Test that an invalid unknown_fields value raises ValueError."""
        with pytest.raises(ValueError, match="unknown_fields must be one of"):
            DataClassConfigBuilder(FlatConfig, unknown_fields="invalid")  # type: ignore[arg-type]


class TestDataClassConfigBuilderPassThrough:
    """Tests for values that are passed through without coercion."""

    def test_complex_type_field_passes_through(self) -> None:
        """Test that generic-typed fields receive values unchanged."""

        @dataclass
        class ListConfig:
            tags: list[str] = field(default_factory=list)

        config = (
            DataClassConfigBuilder(ListConfig).from_dict({"tags": ["a", "b"]}).build()
        )

        assert config.tags == ["a", "b"]

    def test_numeric_pass_through_without_coercion(self) -> None:
        """Test that non-string numeric values are passed through unchanged.

        This documents the explicit pass-through behaviour when a value is
        not a string and cannot be safely coerced.
        """

        @dataclass
        class NumericConfig:
            port: int = 8080

        config = DataClassConfigBuilder(NumericConfig).from_dict({"port": 3.14}).build()

        assert config.port == 3.14


# —— Fluent API & Inheritance Tests ————————————————————————————————


class TestDataClassConfigBuilderFluentAPI:
    """Tests for fluent API and inheritance."""

    def test_fluent_api_returns_self(self, yaml_config_file: Path) -> None:
        """Test that all fluent methods return self for chaining.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        builder = DataClassConfigBuilder(FlatConfig)

        assert builder.from_file(yaml_config_file) is builder
        assert builder.from_dict({"port": 7000}) is builder
        assert builder.set("debug", False) is builder

    def test_inheritance_from_raw_builder(self) -> None:
        """Test that DataClassConfigBuilder is a subclass of RawConfigBuilder.

        Verifies the inheritance relationship: DataClassConfigBuilder
        extends RawConfigBuilder.
        """
        builder = DataClassConfigBuilder(FlatConfig)

        assert isinstance(builder, RawConfigBuilder)

    def test_peek_works(self) -> None:
        """Test that peek() returns the merged dict before build()."""
        builder = DataClassConfigBuilder(FlatConfig).from_dict({"port": 5000})

        peeked = builder.peek()

        assert isinstance(peeked, dict)
        assert peeked["port"] == 5000

    def test_build_dict_works(self) -> None:
        """Test that build_dict() returns a plain dict, not a dataclass."""
        result = (
            DataClassConfigBuilder(FlatConfig).from_dict({"port": 5000}).build_dict()
        )

        assert isinstance(result, dict)
        assert result["port"] == 5000
