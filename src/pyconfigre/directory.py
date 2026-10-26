"""
Directory loading — load all config files from a directory.

Provides :class:`ConfigNamespace` (a read-only, attribute-accessible dict
wrapper) and :func:`load_directory` (loads all supported files, keyed by
filename stem).

Examples
--------
::

    from pyconfigre.directory import load_directory

    ns = load_directory("config/")
    print(ns.database)   # contents of config/database.yaml
    print(ns["server"])   # contents of config/server.json
"""

from pathlib import Path
from typing import Any, Literal

from .exceptions import ConfigLoadError, ConfigNotFoundError
from .loaders import ConfigLoader


class ConfigNamespace:
    """Read-only, attribute-accessible dict wrapper for directory-loaded config.

    Parameters
    ----------
    data : dict[str, Any]
        Mapping of filename stems to loaded configuration dicts.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        object.__setattr__(self, "_data", data)

    def __getattr__(self, key: str) -> Any:
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(
                f"ConfigNamespace has no attribute {key!r}"
            ) from None

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"ConfigNamespace({self._data!r})"

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("ConfigNamespace is read-only")

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict copy of the namespace data.

        Returns
        -------
        dict[str, Any]
            Shallow copy of the internal data mapping.
        """
        return dict(self._data)


def load_directory(
    path: str | Path,
    *,
    recursive: bool = True,
    skip_hidden: bool = True,
    unknown_extensions: Literal["skip", "raise"] = "skip",
) -> ConfigNamespace:
    """
    Load all supported config files from a directory.

    Each file is keyed by its filename stem (e.g. ``database.yaml`` →
    ``"database"``).

    Parameters
    ----------
    path : str | Path
        Directory to load from.
    recursive : bool, optional
        Whether to search subdirectories.  Default is ``True``.
    skip_hidden : bool, optional
        Skip files starting with ``.``.  Default is ``True``.
    unknown_extensions : {"skip", "raise"}, optional
        How to handle files with unsupported extensions.
        Default is ``"skip"``.

    Returns
    -------
    ConfigNamespace
        Attribute-accessible namespace of loaded configs.

    Raises
    ------
    ConfigNotFoundError
        If *path* does not exist.
    ConfigLoadError
        If *path* is not a directory.
    ValueError
        If *unknown_extensions* is ``"raise"`` and an unsupported file
        is found.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigNotFoundError(f"Directory not found: {path}")
    if not path.is_dir():
        raise ConfigLoadError(f"Not a directory: {path}")

    data: dict[str, Any] = {}
    pattern = "**/*" if recursive else "*"

    for file_path in sorted(path.glob(pattern)):
        if not file_path.is_file():
            continue
        if skip_hidden and file_path.name.startswith("."):
            continue

        try:
            ConfigLoader.validate_extension(file_path.suffix)
        except ValueError:
            if unknown_extensions == "raise":
                raise
            continue

        file_data = ConfigLoader.detect_and_load(file_path)
        data[file_path.stem] = file_data

    return ConfigNamespace(data)
