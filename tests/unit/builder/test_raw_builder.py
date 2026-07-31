"""Test suite for pyconfigre.builder.raw_builder — RawConfigBuilder.

This module contains unit tests for RawConfigBuilder fluent API,
file/env/dict sources, the set() method, exception handling, and
fluent API chaining.
"""

import os
from pathlib import Path
from unittest import mock

import pytest

from pyconfigre import RawConfigBuilder
from pyconfigre.exceptions import ConfigLoadError, ConfigNotFoundError

# —— RawConfigBuilder (Parent-class) Tests ————————————————————————————————————————————


class TestRawConfigBuilder:
    """Tests for RawConfigBuilder fluent API."""

    def test_build_dict_empty_pipeline(self) -> None:
        """Test building with no sources returns an empty dict.

        Verifies that a fresh RawConfigBuilder with no sources added
        produces an empty dictionary.
        """
        raw_config = RawConfigBuilder().build_dict()

        assert isinstance(raw_config, dict)
        assert raw_config == {}

    def test_build_dict_from_dict(self) -> None:
        """Test building simple configuration from a plain dictionary.

        Verifies that RawConfigBuilder produces a plain dictionary
        without requiring a Pydantic schema.
        """
        raw_config = (
            RawConfigBuilder().from_dict({"debug": True, "port": 3000}).build_dict()
        )

        assert isinstance(raw_config, dict)
        assert raw_config == {"debug": True, "port": 3000}

    def test_from_file_yaml(self, yaml_config_file: Path) -> None:
        """Test loading configuration from a YAML file.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        raw_config = RawConfigBuilder().from_file(yaml_config_file).build_dict()

        assert raw_config["app_name"] == "test_application_yaml"
        assert raw_config["debug"] is True
        assert raw_config["port"] == 9000

    def test_from_file_json(self, json_config_file: Path) -> None:
        """Test loading configuration from JSON file.

        Parameters
        ----------
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        raw_config = RawConfigBuilder().from_file(json_config_file).build_dict()

        assert raw_config["app_name"] == "test_application_json"
        assert raw_config["debug"] is True

    def test_from_file_toml(self, toml_config_file: Path) -> None:
        """Test loading configuration from a TOML file.

        Parameters
        ----------
        toml_config_file : Path
            Fixture providing a temporary TOML config file.
        """
        raw_config = RawConfigBuilder().from_file(toml_config_file).build_dict()

        assert raw_config["app_name"] == "test_application_toml"
        assert raw_config["debug"] is True

    def test_from_file_optional_missing(self, temp_dir: Path) -> None:
        """Test optional file parameter with missing file.

        Verifies that missing optional files do not raise an error
        and configuration continues with empty state.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        nonexistent = temp_dir / "missing.yaml"

        raw_config = (
            RawConfigBuilder().from_file(nonexistent, optional=True).build_dict()
        )

        assert raw_config == {}

    def test_from_file_required_missing(self, temp_dir: Path) -> None:
        """Test error when required file is missing.

        Verifies that RawConfigBuilder raises ConfigNotFoundError when
        a required configuration file is missing.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        nonexistent = temp_dir / "missing.yaml"

        with pytest.raises(ConfigNotFoundError):
            RawConfigBuilder().from_file(nonexistent)

    def test_from_env(self) -> None:
        """Test loading from environment variables.

        Sets environment variables and verifies they are loaded and
        properly type-parsed by the builder.
        """
        os.environ["RAW_APP_NAME"] = "env_app"
        os.environ["RAW_DEBUG"] = "true"
        os.environ["RAW_PORT"] = "3000"

        try:
            raw_config = RawConfigBuilder().from_env(prefix="RAW_").build_dict()

            assert raw_config["app_name"] == "env_app"
            assert raw_config["debug"] is True
            assert raw_config["port"] == 3000
        finally:
            for key in ["RAW_APP_NAME", "RAW_DEBUG", "RAW_PORT"]:
                del os.environ[key]

    def test_from_dict(self) -> None:
        """Test loading from dictionary.

        Verifies that RawConfigBuilder can load configuration from
        a Python dictionary.
        """
        raw_config = (
            RawConfigBuilder()
            .from_dict({"app_name": "dict_app", "port": 5000})
            .build_dict()
        )

        assert raw_config["app_name"] == "dict_app"
        assert raw_config["port"] == 5000

    def test_from_dict_empty(self) -> None:
        """Test loading an empty dictionary.

        Verifies that merging an empty dict is a no-op and does not disturb
        existing state.
        """
        raw_config = (
            RawConfigBuilder().from_dict({"port": 3000}).from_dict({}).build_dict()
        )

        assert raw_config == {"port": 3000}

    def test_set_value(self) -> None:
        """Test setting individual configuration values.

        Verifies that RawConfigBuilder.set() can set individual
        configuration values.
        """
        raw_config = (
            RawConfigBuilder().set("app_name", "set_app").set("port", 7000).build_dict()
        )

        assert raw_config["app_name"] == "set_app"
        assert raw_config["port"] == 7000

    def test_set_nested_value(self) -> None:
        """Test setting nested configuration values.

        Verifies that RawConfigBuilder.set() supports dot notation
        for setting nested configuration values.
        """
        raw_config = (
            RawConfigBuilder()
            .set("server.host", "example.com")
            .set("server.port", 5432)
            .build_dict()
        )

        assert raw_config["server"]["host"] == "example.com"
        assert raw_config["server"]["port"] == 5432

    def test_multiple_sources_priority(
        self, yaml_config_file: Path, json_config_file: Path
    ) -> None:
        """Test priority merging of multiple sources.

        Verifies that when loading from multiple sources, later sources
        override earlier ones (YAML → JSON → dict).

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        raw_config = (
            RawConfigBuilder()
            .from_file(yaml_config_file)
            .from_file(json_config_file)
            .from_dict({"port": 7000})
            .build_dict()
        )

        assert raw_config["app_name"] == "test_application_json"
        assert raw_config["port"] == 7000

    def test_full_priority_chain(self, yaml_config_file: Path) -> None:
        """Test the full file → env → dict → set() priority chain.

        Each source overrides the one before it.  The YAML fixture provides
        ``app_name``, ``debug`` and ``port``; env overrides ``debug``;
        dict overrides ``port``; and set() overrides ``app_name``.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        os.environ["PRIORITY_DEBUG"] = "false"

        try:
            raw_config = (
                RawConfigBuilder()
                .from_file(yaml_config_file)
                .from_env(prefix="PRIORITY_")
                .from_dict({"port": 4000})
                .set("app_name", "chain_override_app")
                .build_dict()
            )

            assert raw_config["app_name"] == "chain_override_app"
            assert raw_config["debug"] is False
            assert raw_config["port"] == 4000
        finally:
            del os.environ["PRIORITY_DEBUG"]

    def test_get_raw_data(self, yaml_config_file: Path) -> None:
        """Test that get_raw_data() emits DeprecationWarning and returns
        the same result as peek().

        ``get_raw_data()`` is a deprecated alias for ``peek()`` as of v0.1.1.
        This test verifies both that the warning is emitted and that the
        return value equals peek().

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        raw_config_builder = RawConfigBuilder().from_file(yaml_config_file)
        raw_peeked = raw_config_builder.peek()

        with pytest.warns(DeprecationWarning, match="get_raw_data\\(\\) is deprecated"):
            raw_data = raw_config_builder.get_raw_data()

        assert isinstance(raw_data, dict)
        assert raw_data["app_name"] == "test_application_yaml"
        assert raw_data["debug"] is True
        assert raw_data == raw_peeked  # values must be equal
        assert raw_data is not raw_peeked  # must be a copy, not the same reference

    def test_fluent_api_chaining(self, yaml_config_file: Path) -> None:
        """Test fluent API method chaining.

        Verifies that RawConfigBuilder methods return self for method
        chaining in a fluent API style.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        raw_config = (
            RawConfigBuilder()
            .from_file(yaml_config_file)
            .set("port", 8888)
            .from_dict({"debug": False})
            .build_dict()
        )

        assert raw_config["app_name"] == "test_application_yaml"
        assert raw_config["port"] == 8888
        assert raw_config["debug"] is False


class TestRawConfigBuilderFromFile:
    """Tests for from_file extension and existence ordering."""

    def test_from_file_validates_extension_before_existence(
        self, temp_dir: Path
    ) -> None:
        """Test that extension is validated before checking file existence.

        A file with an unsupported extension that also does not exist should
        raise ValueError (unsupported extension), not ConfigNotFoundError
        (file missing).  The extension error is more actionable at development
        time.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        missing_with_bad_ext = temp_dir / "config.xyz"
        # File does NOT exist — but extension is bad, so ValueError must come first

        with pytest.raises(ValueError, match="Unsupported file format"):
            RawConfigBuilder().from_file(missing_with_bad_ext)

    def test_from_file_optional_bad_extension_still_raises(
        self, temp_dir: Path
    ) -> None:
        """Test that optional=True does not suppress unsupported-extension errors.

        ``optional`` silences missing-file errors only.  An unsupported extension
        is a programmer error and must always raise regardless of ``optional``.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        missing_with_bad_ext = temp_dir / "config.xyz"

        with pytest.raises(ValueError, match="Unsupported file format"):
            RawConfigBuilder().from_file(missing_with_bad_ext, optional=True)


class TestRawConfigBuilderExceptionHandling:
    """Tests exception handling and edge cases in RawConfigBuilder."""

    def test_from_file_with_unsupported_extension(self, temp_dir: Path) -> None:
        """Test error when file has unsupported extension.

        Extension is validated before existence check, so this raises
        ValueError even when the file exists.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        unsupported_file = temp_dir / "config.unknown"
        unsupported_file.write_text("some content")

        raw_config_builder = RawConfigBuilder()

        with pytest.raises(ValueError, match="Unsupported file format"):
            raw_config_builder.from_file(unsupported_file)

    def test_from_file_generic_exception_wrapping(self, temp_dir: Path) -> None:
        """Test that generic exceptions are wrapped in ConfigLoadError.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"debug": true}')

        raw_config_builder = RawConfigBuilder()

        with mock.patch(
            "pyconfigre.builder.raw_builder.ConfigLoader.detect_and_load"
        ) as mock_load:
            mock_load.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(ConfigLoadError, match="Failed to load configuration"):
                raw_config_builder.from_file(config_file)

    def test_from_file_propagates_value_error(self, temp_dir: Path) -> None:
        """Test that ValueError from unsupported extension is propagated.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        unsupported_file = temp_dir / "config.xyz"
        unsupported_file.write_text("content")

        raw_config_builder = RawConfigBuilder()

        with pytest.raises(ValueError):
            raw_config_builder.from_file(unsupported_file)

    def test_from_file_propagates_config_load_error(self, temp_dir: Path) -> None:
        """Test that ConfigLoadError from loaders is propagated.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"debug": true}')

        raw_config_builder = RawConfigBuilder()

        with mock.patch(
            "pyconfigre.builder.raw_builder.ConfigLoader.detect_and_load"
        ) as mock_load:
            mock_load.side_effect = ConfigLoadError("Parse error")

            with pytest.raises(ConfigLoadError, match="Parse error"):
                raw_config_builder.from_file(config_file)


class TestRawConfigBuilderSetMethod:
    """Tests set method with dot notation."""

    def test_set_simple_key(self) -> None:
        """Test setting a simple key."""
        raw_config_builder = RawConfigBuilder()
        raw_config_builder.set("app_name", "my_app")

        raw_peeked = raw_config_builder.peek()
        assert raw_peeked["app_name"] == "my_app"

    def test_set_nested_key_with_dot_notation(self) -> None:
        """Test setting nested key using dot notation."""
        raw_config_builder = RawConfigBuilder()
        raw_config_builder.set("database.host", "localhost")
        raw_config_builder.set("database.port", 5432)

        raw_peeked = raw_config_builder.peek()
        assert raw_peeked["database"]["host"] == "localhost"
        assert raw_peeked["database"]["port"] == 5432

    def test_set_deeply_nested_key(self) -> None:
        """Test setting a deeply nested key."""
        raw_config_builder = RawConfigBuilder()
        raw_config_builder.set("app.db.connection.host", "db.example.com")

        raw_peeked = raw_config_builder.peek()
        assert raw_peeked["app"]["db"]["connection"]["host"] == "db.example.com"

    def test_set_overwrites_existing_key(self) -> None:
        """Test that set overwrites existing values."""
        raw_config_builder = RawConfigBuilder()
        raw_config_builder.set("debug", False)
        raw_config_builder.set("debug", True)

        raw_peeked = raw_config_builder.peek()
        assert raw_peeked["debug"] is True

    def test_set_method_returns_self(self) -> None:
        """Test that set method returns self for fluent chaining."""
        raw_config_builder = RawConfigBuilder()
        raw_config = raw_config_builder.set("key", "value")

        assert raw_config is raw_config_builder

    def test_set_raises_type_error_on_scalar_intermediate(self) -> None:
        """Test that set() raises TypeError with a clear message
        when a dot-notation path segment exists but is not a dict.

        The error message must include:
        - the full requested key path
        - the name of the offending intermediate segment
        - the actual type that was found
        """
        raw_config_builder = RawConfigBuilder()
        raw_config_builder._data = {"database": "not_a_dict"}

        with pytest.raises(TypeError) as exc_info:
            raw_config_builder.set("database.host", "localhost")

        message = str(exc_info.value)
        assert "database.host" in message
        assert "database" in message
        assert "str" in message

    def test_set_raises_type_error_on_deeply_nested_scalar(self) -> None:
        """Test TypeError is raised at the correct depth for deep paths."""
        raw_config_builder = RawConfigBuilder()
        raw_config_builder._data = {"a": {"b": "scalar"}}

        with pytest.raises(TypeError) as exc_info:
            raw_config_builder.set("a.b.c", "value")

        message = str(exc_info.value)
        assert "a.b.c" in message
        assert "a.b" in message
        assert "str" in message


class TestRawConfigBuilderFluentAPI:
    """Test fluent API chaining."""

    def test_chaining_all_methods(self, temp_dir: Path) -> None:
        """Test chaining multiple methods.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"app_name": "file_app"}')

        os.environ["FLUENT_RAW_DEBUG"] = "true"

        try:
            raw_config = (
                RawConfigBuilder()
                .from_file(config_file)
                .from_env(prefix="FLUENT_RAW_")
                .set("port", 7000)
                .build_dict()
            )

            assert raw_config["app_name"] == "file_app"
            assert raw_config["debug"] is True
            assert raw_config["port"] == 7000
        finally:
            del os.environ["FLUENT_RAW_DEBUG"]

    def test_multiple_from_dict_calls(self) -> None:
        """Test multiple from_dict calls with proper priority."""
        raw_config = (
            RawConfigBuilder()
            .from_dict({"debug": False, "port": 8000})
            .from_dict({"debug": True})
            .from_dict({"port": 9000})
            .build_dict()
        )

        assert raw_config["debug"] is True
        assert raw_config["port"] == 9000

    def test_get_raw_data(self, temp_dir: Path) -> None:
        """Test get_raw_data emits DeprecationWarning and returns a copy.

        Verifies that:
        - ``DeprecationWarning`` is emitted on every call
        - each call returns an independent copy (mutations do not bleed)
        - the returned data matches the builder's internal state

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"port": 3000}')

        raw_config_builder = RawConfigBuilder().from_file(config_file)

        with pytest.warns(DeprecationWarning, match="get_raw_data\\(\\) is deprecated"):
            raw1 = raw_config_builder.get_raw_data()

        with pytest.warns(DeprecationWarning):
            raw2 = raw_config_builder.get_raw_data()

        assert raw1 == raw2
        assert raw1 is not raw2

        raw1["port"] = 9999

        with pytest.warns(DeprecationWarning):
            raw3 = raw_config_builder.get_raw_data()

        assert raw3["port"] == 3000

    def test_peek_returns_copy(self, temp_dir: Path) -> None:
        """Test that peek() returns a copy equal to get_raw_data().

        ``peek()`` is the preferred name; ``get_raw_data()`` is its
        deprecated alias.  Both must return equal, independent copies.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"port": 4000}')

        raw_config_builder = RawConfigBuilder().from_file(config_file)

        raw_peeked = raw_config_builder.peek()

        with pytest.warns(DeprecationWarning):
            raw = raw_config_builder.get_raw_data()

        assert raw_peeked == raw
        assert raw_peeked is not raw

    def test_peek_is_nondestructive(self, temp_dir: Path) -> None:
        """Test that mutating the dict returned by peek() does not affect
        the builder's internal state.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        config_file = temp_dir / "config.json"
        config_file.write_text('{"port": 5000}')

        raw_config_builder = RawConfigBuilder().from_file(config_file)

        snapshot = raw_config_builder.peek()
        snapshot["port"] = 99999

        assert raw_config_builder.peek()["port"] == 5000

    def test_build_dict_returns_copy(self) -> None:
        """Test that build_dict() returns a copy, not a reference.

        Mutating the returned dictionary must not affect the
        builder's internal state, allowing build_dict() to be called
        multiple times with consistent results.
        """
        raw_config_builder = RawConfigBuilder().from_dict({"port": 6000})

        first = raw_config_builder.build_dict()
        first["port"] = 99999

        second = raw_config_builder.build_dict()

        assert second["port"] == 6000
        assert first is not second

    def test_build_dict_called_multiple_times_returns_consistent_copies(self) -> None:
        """Test that build_dict() produces equal results on repeated call.

        The internal method must be independent — calling it multiple
        times without changing the pipeline must return equal dictionaries.
        """
        raw_config_builder = RawConfigBuilder().from_dict({"debug": True, "port": 3000})

        first = raw_config_builder.build_dict()
        second = raw_config_builder.build_dict()

        assert first == second
        assert first is not second
