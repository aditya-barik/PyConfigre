"""JSON configuration loader."""

import json
from pathlib import Path
from typing import Any

from ..exceptions import ConfigLoadError
from .base import BaseLoader


class JSONLoader(BaseLoader):
    """
    Load configuration from JSON files.

    Supports standard JSON format with automatic dict validation
    and comprehensive error handling.

    Examples
    --------
    >>> loader = JSONLoader()
    >>> config = loader("config.json")
    >>> config
    {'debug': False, 'port': 8000}
    """

    def __call__(self, path: str | Path) -> dict[str, Any]:
        """
        Load configuration from a JSON file.

        Parameters
        ----------
        path : str | Path
            Path to JSON file.

        Returns
        -------
        dict[str, Any]
            Dictionary containing configuration.

        Raises
        ------
        ConfigLoadError
            If file cannot be loaded or parsed.
        """
        try:
            file_path = self._check_file_exists(path)

            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return self._validate_dict(data)

        except ConfigLoadError:
            raise
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Failed to parse JSON file {path}: {e}") from e
        except Exception as e:
            raise ConfigLoadError(f"Failed to load JSON file {path}: {e}") from e
