"""Test suite for JSON loader."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pyconfigre.exceptions import ConfigLoadError
from pyconfigre.loaders import JSONLoader


class TestJSONLoader:
    """Tests for JSONLoader class."""

    def test_load_json_file(self, json_config_file: Path) -> None:
        """Test loading valid JSON file.

        Parameters
        ----------
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        loader = JSONLoader()
        config = loader(json_config_file)

        assert config["app_name"] == "test_application_json"
        assert config["debug"] is True
        assert config["port"] == 9000

    def test_json_file_not_found(self, temp_dir: Path) -> None:
        """Test error handling for missing JSON file.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        loader = JSONLoader()
        nonexistent_file = temp_dir / "nonexistent.json"

        with pytest.raises(ConfigLoadError, match="File not found"):
            loader(nonexistent_file)

    def test_json_invalid_syntax(self, temp_dir: Path) -> None:
        """Test error handling for invalid JSON syntax.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{invalid json content")

        loader = JSONLoader()

        with pytest.raises(ConfigLoadError, match="Failed to parse"):
            loader(invalid_file)

    def test_json_non_dict_root(self, temp_dir: Path) -> None:
        """Test handling of JSON with non-dict root.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        non_dict_file = temp_dir / "non_dict.json"
        non_dict_file.write_text('["array", "root"]')

        loader = JSONLoader()

        with pytest.raises(ConfigLoadError, match="not a dictionary"):
            loader(non_dict_file)

    def test_json_general_exception_handling(self, temp_dir: Path) -> None:
        """Test JSONLoader handles general exceptions during loading.

        This tests the exception handler that catches non-JSONDecodeError exceptions.
        """
        loader = JSONLoader()
        config_file = temp_dir / "config.json"
        config_file.write_text('{"key": "value"}')

        # Mock json.load to raise a generic Exception
        with patch("json.load", side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(ConfigLoadError, match="Failed to load JSON"):
                loader(config_file)

    def test_json_decode_error_handling(self, temp_dir: Path) -> None:
        """Test JSONLoader handles JSONDecodeError during parsing.

        This tests the specific JSON decoding error handler.
        """
        loader = JSONLoader()
        config_file = temp_dir / "config.json"
        config_file.write_text('{"key": "value"}')

        # Mock json.load to raise JSONDecodeError
        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            with pytest.raises(ConfigLoadError, match="Failed to parse JSON"):
                loader(config_file)

    def test_json_config_load_error_passthrough(self, temp_dir: Path) -> None:
        """Test that ConfigLoadError is re-raised as-is.

        This tests the `except ConfigLoadError: raise` branch.
        """
        loader = JSONLoader()
        config_file = temp_dir / "config.json"
        config_file.write_text('{"key": "value"}')

        # Mock _validate_dict to raise ConfigLoadError
        with patch.object(
            loader, "_validate_dict", side_effect=ConfigLoadError("Validation error")
        ):
            with pytest.raises(ConfigLoadError, match="Validation error"):
                loader(config_file)
