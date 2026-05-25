"""Tests for BaseLoader abstract base class."""

import tempfile
from pathlib import Path

import pytest

from pyconfigre.exceptions import ConfigNotFoundError, ConfigValidationError
from pyconfigre.loaders import BaseLoader, ENVLoader, JSONLoader, TOMLLoader, YAMLLoader


class TestBaseLoader:
    """Test BaseLoader common functionality and error paths."""

    def test___call__raises_not_implemented_error(self) -> None:
        """Test BaseLoader.__call__ raises NotImplementedError.

        This tests the abstract method enforcement.
        """

        # Create a subclass that overrides __call__ with default behavior
        class MinimalLoader(BaseLoader):
            def __call__(self, path):
                # Call parent to trigger NotImplementedError
                return super().__call__(path)

        loader = MinimalLoader()

        with pytest.raises(NotImplementedError, match="Subclasses must implement"):
            loader("any_path")

    def test__validate_dict_with_valid_dict(self) -> None:
        """Test successful validation of valid dict."""
        loader = ENVLoader()
        data = {"key": "value", "nested": {"inner": "data"}}
        result = loader._validate_dict(data)

        assert result == data
        assert result is data

    def test__validate_dict_with_integer_raises_error(self) -> None:
        """Test validation error when data is an integer."""
        loader = JSONLoader()

        with pytest.raises(ConfigValidationError, match="not a dictionary"):
            loader._validate_dict(123)

    def test__validate_dict_with_list_raises_error(self) -> None:
        """Test validation error when data is a list."""
        loader = TOMLLoader()

        with pytest.raises(ConfigValidationError, match="not a dictionary"):
            loader._validate_dict([1, 2, 3])

    def test__validate_dict_with_string_raises_error(self) -> None:
        """Test validation error when data is a string."""
        loader = YAMLLoader()

        with pytest.raises(ConfigValidationError, match="not a dictionary"):
            loader._validate_dict("not a dict")

    def test__validate_dict_with_none_returns_empty(self) -> None:
        """Test that None input returns empty dict."""
        loader = JSONLoader()
        result = loader._validate_dict(None)

        assert result == {}
        assert isinstance(result, dict)

    def test_validate_dict_empty_dict(self) -> None:
        """Test validation of empty dictionary."""
        loader = ENVLoader()
        result = loader._validate_dict({})

        assert result == {}
        assert len(result) == 0

    def test__check_file_exists_with_existing_file(self) -> None:
        """Test successful file existence check."""
        loader = JSONLoader()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            result = loader._check_file_exists(temp_path)
            assert isinstance(result, Path)
            assert result.exists()
            assert str(result) == temp_path
        finally:
            Path(temp_path).unlink()

    def test__check_file_exists_with_path_object(self) -> None:
        """Test file existence check with Path object."""
        loader = JSONLoader()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = loader._check_file_exists(temp_path)
            assert isinstance(result, Path)
            assert result == temp_path
        finally:
            temp_path.unlink()

    def test__check_file_exists_nonexistent_raises_error(self) -> None:
        """Test error when file doesn't exist."""
        loader = TOMLLoader()

        with pytest.raises(ConfigNotFoundError, match="File not found"):
            loader._check_file_exists("/nonexistent/path/to/file.json")

    def test__check_file_exists_with_invalid_path(self) -> None:
        """Test error with invalid/empty path string."""
        loader = YAMLLoader()

        # Empty string resolves to current directory, which exists
        # So we test with a path that definitely doesn't exist
        with pytest.raises(ConfigNotFoundError):
            loader._check_file_exists("/" * 100 + "nonexistent")
