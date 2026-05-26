"""TOML configuration loader."""

import sys
from pathlib import Path
from typing import Any

from ..exceptions import ConfigLoadError
from .base import BaseLoader

# TOML support for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:  # pragma: no cover
        import tomli as tomllib  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover
        tomllib = None


class TOMLLoader(BaseLoader):
    """
    Load configuration from TOML files.

    Supports standard TOML format with Python version compatibility
    (uses tomllib for Python 3.11+ and tomli for earlier versions).

    Examples
    --------
    >>> loader = TOMLLoader()
    >>> config = loader("config.toml")
    >>> config
    {'server': {'debug': False, 'port': 8000}}
    """

    def __call__(self, path: str | Path) -> dict[str, Any]:
        """
        Load configuration from a TOML file.

        Parameters
        ----------
        path : str | Path
            Path to TOML file.

        Returns
        -------
        dict[str, Any]
            Dictionary containing configuration.

        Raises
        ------
        ConfigLoadError
            If file cannot be loaded or parsed.
        ImportError
            If tomli is not installed (Python < 3.11).
        """
        if tomllib is None:
            raise ImportError(
                "TOML support requires 'tomli' package for Python < 3.11. "
                "Install with: pip install pyconfig[toml]"
            )

        try:
            file_path = self._check_file_exists(path)

            with file_path.open("rb") as f:
                data = tomllib.load(f)
                return self._validate_dict(data)

        except ConfigLoadError:
            raise
        except Exception as e:
            if "tomllib" in str(type(e)) or "tomli" in str(type(e)):
                raise ConfigLoadError(f"Failed to parse TOML file {path}: {e}") from e
            raise ConfigLoadError(f"Failed to load TOML file {path}: {e}") from e
