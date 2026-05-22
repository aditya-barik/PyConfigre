"""Test suite for YAML loader."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from pyconfigr.exceptions import ConfigLoadError
from pyconfigr.loaders import ConfigLoader, YAMLLoader


class TestYAMLLoader:
    """Tests for YAMLLoader class."""

    def test_load_yaml_file(self, yaml_config_file: Path) -> None:
        """Test loading valid YAML file.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        loader = YAMLLoader()
        config = loader(yaml_config_file)

        assert config["app_name"] == "test_application_yaml"
        assert config["debug"] is True
        assert config["port"] == 9000
        assert config["server"]["host"] == "localhost"

    def test_load_yaml_with_singleton(self, yaml_config_file: Path) -> None:
        """Test loading YAML using singleton instance.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config = ConfigLoader.get_loader("yaml")(yaml_config_file)

        assert config["app_name"] == "test_application_yaml"
        assert config["debug"] is True

    def test_yaml_file_not_found(self, temp_dir: Path) -> None:
        """Test error handling for missing YAML file.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        loader = YAMLLoader()
        nonexistent_file = temp_dir / "nonexistent.yaml"

        with pytest.raises(ConfigLoadError, match="File not found"):
            loader(nonexistent_file)

    def test_yaml_empty_file(self, temp_dir: Path) -> None:
        """Test handling of empty YAML file.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        empty_file = temp_dir / "empty.yaml"
        empty_file.write_text("")

        loader = YAMLLoader()
        config = loader(empty_file)

        assert config == {}

    def test_yaml_invalid_syntax(self, temp_dir: Path) -> None:
        """Test error handling for invalid YAML syntax.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: : :")

        loader = YAMLLoader()

        with pytest.raises(ConfigLoadError, match="Failed to parse"):
            loader(invalid_file)

    def test_yaml_general_exception_handling(self, temp_dir: Path) -> None:
        """Test YAMLLoader handles general exceptions during loading.

        This tests the exception handler that catches non-YAMLError exceptions.
        """
        loader = YAMLLoader()
        config_file = temp_dir / "config.yaml"
        config_file.write_text("key: value")

        # Mock yaml.safe_load to raise a generic Exception
        with patch("yaml.safe_load", side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(ConfigLoadError, match="Failed to load YAML"):
                loader(config_file)

    def test_yaml_parse_error_handling(self, temp_dir: Path) -> None:
        """Test YAMLLoader handles YAMLError during parsing.

        This tests the specific YAML parsing error handler.
        """
        loader = YAMLLoader()
        config_file = temp_dir / "config.yaml"
        config_file.write_text("key: value")

        # Mock yaml.safe_load to raise YAMLError
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Parse error")):
            with pytest.raises(ConfigLoadError, match="Failed to parse YAML"):
                loader(config_file)

    def test_yaml_config_load_error_passthrough(self, temp_dir: Path) -> None:
        """Test that ConfigLoadError is re-raised as-is.

        This tests the `except ConfigLoadError: raise` branch.
        """
        loader = YAMLLoader()
        config_file = temp_dir / "config.yaml"
        config_file.write_text("key: value")

        # Mock _validate_dict to raise ConfigLoadError
        with patch.object(
            loader, "_validate_dict", side_effect=ConfigLoadError("Validation error")
        ):
            with pytest.raises(ConfigLoadError, match="Validation error"):
                loader(config_file)
