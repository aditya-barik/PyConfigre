"""YAML configuration loader."""

from pathlib import Path
from typing import Any

import yaml

from ..exceptions import ConfigLoadError, ConfigNotFoundError, ConfigValidationError
from .base import BaseLoader


class YAMLLoader(BaseLoader):
    """
    Load configuration from YAML files.

    Supports standard YAML format with safe loading to prevent
    code execution vulnerabilities.

    Examples
    --------
    >>> loader = YAMLLoader()
    >>> config = loader("config.yaml")
    >>> config
    {'server': {'debug': False, 'port': 8000}}
    """

    def __call__(self, path: str | Path) -> dict[str, Any]:
        """
        Load configuration from a YAML file.

        Parameters
        ----------
        path : str | Path
            Path to YAML file.

        Returns
        -------
        dict[str, Any]
            Dictionary containing configuration.

        Raises
        ------
        ConfigNotFoundError
            If the file does not exist.
        ConfigLoadError
            If the file cannot be read or parsed.
        ConfigValidationError
            If the parsed content is not a dictionary.
        """
        try:
            file_path = self._check_file_exists(path)

            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return self._validate_dict(data)

        except (ConfigLoadError, ConfigNotFoundError, ConfigValidationError):
            raise
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Failed to parse YAML file {path}: {e}") from e
        except Exception as e:
            raise ConfigLoadError(f"Failed to load YAML file {path}: {e}") from e
