"""Tests for exception classes."""

import pytest

from pyconfigre.exceptions import (
    ConfigError,
    ConfigLoadError,
    ConfigNotFoundError,
    ConfigValidationError,
)


class TestConfigError:
    """Test ConfigError base exception class."""

    def test_config_error_creation(self) -> None:
        """Test creating ConfigError."""
        error = ConfigError("Test error message")
        assert isinstance(error, Exception)
        assert error.__class__ == ConfigError
        assert str(error) == "Test error message"

    def test_config_error_with_empty_message(self) -> None:
        """Test ConfigError with empty message."""
        error = ConfigError()
        assert isinstance(error, Exception)
        assert error.__class__ == ConfigError
        assert error.args == ()

    def test_config_error_inheritance(self) -> None:
        """Test that ConfigError is base for other exceptions."""
        assert issubclass(ConfigLoadError, ConfigError)
        assert issubclass(ConfigValidationError, ConfigError)
        assert issubclass(ConfigNotFoundError, ConfigError)

    def test_config_error_raise_and_catch(self) -> None:
        """Test raising and catching ConfigError."""
        with pytest.raises(ConfigError):
            raise ConfigError("Test")

    def test_config_error_catch_subclass_with_parent(self) -> None:
        """Test catching subclass with parent exception handler."""
        with pytest.raises(ConfigError):
            raise ConfigLoadError("Test load error")


class TestConfigLoadError:
    """Test ConfigLoadError exception class."""

    def test_config_load_error_creation(self) -> None:
        """Test creating ConfigLoadError."""
        error = ConfigLoadError("Failed to load config")
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigError)
        assert error.__class__ == ConfigLoadError
        assert str(error) == "Failed to load config"

    def test_config_load_error_with_cause(self) -> None:
        """Test ConfigLoadError with exception chain."""
        original_error = None
        try:
            raise ValueError("Invalid JSON")
        except ValueError as e:
            original_error = e
            error = ConfigLoadError("Failed to load")
            error.__cause__ = e

        assert error.__cause__ is original_error

    def test_config_load_error_raise_and_catch(self) -> None:
        """Test raising and catching ConfigLoadError."""
        with pytest.raises(ConfigLoadError):
            raise ConfigLoadError("Load failed")

    def test_config_load_error_message_formatting(self) -> None:
        """Test ConfigLoadError with formatted message."""
        path = "config.json"
        error = ConfigLoadError(f"Failed to load {path}: Invalid syntax")
        assert path in str(error)

    def test_config_load_error_catch_with_parent(self) -> None:
        """Test catching ConfigLoadError as ConfigError."""
        with pytest.raises(ConfigError):
            raise ConfigLoadError("Test")


class TestConfigValidationError:
    """Test ConfigValidationError exception class."""

    def test_config_validation_error_creation(self) -> None:
        """Test creating ConfigValidationError."""
        error = ConfigValidationError("Invalid configuration")
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigError)
        assert error.__class__ == ConfigValidationError
        assert str(error) == "Invalid configuration"

    def test_config_validation_error_with_details(self) -> None:
        """Test ConfigValidationError with detailed message."""
        error = ConfigValidationError(
            "Config validation failed for AppConfig: port is required"
        )
        assert "AppConfig" in str(error)
        assert "port" in str(error)

    def test_config_validation_error_raise_and_catch(self) -> None:
        """Test raising and catching ConfigValidationError."""
        with pytest.raises(ConfigValidationError):
            raise ConfigValidationError("Validation failed")

    def test_config_validation_error_catch_with_parent(self) -> None:
        """Test catching ConfigValidationError as ConfigError."""
        with pytest.raises(ConfigError):
            raise ConfigValidationError("Test")


class TestConfigNotFoundError:
    """Test ConfigNotFoundError exception class."""

    def test_config_not_found_error_creation(self) -> None:
        """Test creating ConfigNotFoundError."""
        error = ConfigNotFoundError("File not found: config.yaml")
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigError)
        assert error.__class__ == ConfigNotFoundError
        assert str(error) == "File not found: config.yaml"

    def test_config_not_found_error_with_path(self) -> None:
        """Test ConfigNotFoundError with file path."""
        path = "/etc/app/config.json"
        error = ConfigNotFoundError(f"File not found: {path}")
        assert path in str(error)

    def test_config_not_found_error_raise_and_catch(self) -> None:
        """Test raising and catching ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError):
            raise ConfigNotFoundError("File missing")

    def test_config_not_found_error_catch_with_parent(self) -> None:
        """Test catching ConfigNotFoundError as ConfigError."""
        with pytest.raises(ConfigError):
            raise ConfigNotFoundError("Test")

    def test_config_not_found_error_with_cause(self) -> None:
        """Test ConfigNotFoundError with exception chain."""
        original_error = None
        try:
            raise FileNotFoundError("config.yaml")
        except FileNotFoundError as e:
            original_error = e
            error = ConfigNotFoundError("Configuration file missing")
            error.__cause__ = e

        assert error.__cause__ is original_error


class TestExceptionHierarchy:
    """Test exception class hierarchy and relationships."""

    def test_all_exceptions_inherit_from_exception(self) -> None:
        """Test that all config exceptions inherit from Exception."""
        assert issubclass(ConfigError, Exception)
        assert issubclass(ConfigLoadError, Exception)
        assert issubclass(ConfigValidationError, Exception)
        assert issubclass(ConfigNotFoundError, Exception)

    def test_exception_catching_with_broad_handler(self) -> None:
        """Test catching all config errors with single handler."""
        errors = [
            ConfigLoadError("Load error"),
            ConfigValidationError("Validation error"),
            ConfigNotFoundError("Not found error"),
        ]

        for error in errors:
            with pytest.raises(ConfigError):
                raise error

    def test_exception_messages_preserved_in_chain(self) -> None:
        """Test that exception messages are preserved in exception chains."""
        original_msg = "Original error"
        wrapped_msg = "Wrapped error"

        original_error = None
        try:
            raise ValueError(original_msg)
        except ValueError as e:
            original_error = e  # noqa: F841
            error = ConfigLoadError(wrapped_msg)
            error.__cause__ = e

        assert wrapped_msg in str(error)
        assert original_msg in str(error.__cause__)
