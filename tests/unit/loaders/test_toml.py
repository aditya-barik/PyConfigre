"""Test suite for TOML loader."""

from pathlib import Path
from unittest.mock import patch

import pytest

from pyconfigr.exceptions import ConfigLoadError
from pyconfigr.loaders import TOMLLoader


class TestTOMLLoader:
    """Tests for TOMLLoader class."""

    def test_load_toml_file(self, toml_config_file: Path) -> None:
        """Test loading valid TOML file.

        Parameters
        ----------
        toml_config_file : Path
            Fixture providing a temporary TOML config file.
        """
        loader = TOMLLoader()
        config = loader(toml_config_file)

        assert config["app_name"] == "test_application_toml"
        assert config["debug"] is True
        assert config["port"] == 9000

    def test_toml_file_not_found(self, temp_dir: Path) -> None:
        """Test error handling for missing TOML file.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        loader = TOMLLoader()
        nonexistent_file = temp_dir / "nonexistent.toml"

        with pytest.raises(ConfigLoadError, match="File not found"):
            loader(nonexistent_file)

    def test_toml_invalid_syntax(self, temp_dir: Path) -> None:
        """Test error handling for invalid TOML syntax.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        invalid_file = temp_dir / "invalid.toml"
        invalid_file.write_text("invalid toml = = = content")

        loader = TOMLLoader()

        with pytest.raises(ConfigLoadError, match="Failed to parse"):
            loader(invalid_file)


class TestTOMLLoaderImportError:
    """Test TOML loader when tomllib is not available."""

    def test_toml_tomllib_not_available(self, temp_dir: Path) -> None:
        """Test error when tomllib/tomli is not available.

        This covers the case where tomllib is None (lines 54-58).
        """
        # Mock pyconfigr.loaders.toml.tomllib to be None
        with patch("pyconfigr.loaders.toml.tomllib", None):
            loader = TOMLLoader()
            config_file = temp_dir / "config.toml"
            config_file.write_text("key = 'value'")

            with pytest.raises(ImportError, match="TOML support requires"):
                loader(config_file)


class TestTOMLLoaderExceptionHandling:
    """Test TOML loader exception handling."""

    def test_toml_with_tomllib_parse_error(self, temp_dir: Path) -> None:
        """Test TOML loader with tomllib-specific parse exception (line 57).

        This covers the path where "tomllib" in str(type(e)) is True.
        """
        loader = TOMLLoader()
        config_file = temp_dir / "config.toml"
        config_file.write_text("key = 'value'")

        # Create a mock exception that looks like tomllib error
        class MockTOMLDecodeError(Exception):
            """Mock tomllib.TOMLDecodeError."""

            pass

        mock_error = MockTOMLDecodeError("TOML parsing failed")
        # Set a type name that contains 'tomllib'
        mock_error.__class__.__module__ = "tomllib"

        with patch("pyconfigr.loaders.toml.tomllib.load") as mock_load:
            mock_load.side_effect = mock_error

            with pytest.raises(ConfigLoadError, match="Failed to parse TOML"):
                loader(config_file)

    def test_toml_with_generic_exception(self, temp_dir: Path) -> None:
        """Test TOML loader with generic non-tomllib exception (line 70).

        This covers the path where the generic exception handler is triggered.
        """
        loader = TOMLLoader()
        config_file = temp_dir / "config.toml"
        config_file.write_text("key = 'value'")

        with patch("pyconfigr.loaders.toml.tomllib.load") as mock_load:
            mock_load.side_effect = OSError("I/O Error")

            with pytest.raises(ConfigLoadError, match="Failed to load TOML"):
                loader(config_file)

    def test_toml_with_tomli_parse_error(self, temp_dir: Path) -> None:
        """Test TOML loader with tomli-specific parse exception.

        This covers the case where "tomli" in str(type(e)) is True.
        """
        loader = TOMLLoader()
        config_file = temp_dir / "config.toml"
        config_file.write_text("key = 'value'")

        # Create a mock exception that looks like tomli error
        class MockTomliDecodeError(Exception):
            """Mock tomli.TOMLDecodeError."""

            pass

        mock_error = MockTomliDecodeError("TOML parsing failed")
        # Set a type name that contains 'tomli'
        mock_error.__class__.__module__ = "tomli"

        with patch("pyconfigr.loaders.toml.tomllib.load") as mock_load:
            mock_load.side_effect = mock_error

            with pytest.raises(ConfigLoadError, match="Failed to parse TOML"):
                loader(config_file)

    def test_toml_config_load_error_re_raised(self, temp_dir: Path) -> None:
        """Test TOML loader re-raises ConfigLoadError (line 70).

        This covers the case where ConfigLoadError is raised in the try block
        and then re-raised in the except ConfigLoadError block.
        """
        loader = TOMLLoader()
        config_file = temp_dir / "config.toml"
        config_file.write_text("key = 'value'")

        # Mock _validate_dict to raise ConfigLoadError
        with patch.object(loader, "_validate_dict") as mock_validate:
            mock_validate.side_effect = ConfigLoadError("Validation failed")

            with pytest.raises(ConfigLoadError, match="Validation failed"):
                loader(config_file)
