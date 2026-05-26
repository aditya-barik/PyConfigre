"""Configuration loader manager with auto-detection and registry management."""

import copy
from pathlib import Path
from typing import Any

from .base import BaseLoader


class ConfigLoader:
    """
    Unified configuration loader with auto-detection and registry management.

    Manages loader instantiation and delegation based on file extensions.
    Supports dynamic loader registration for maximum extensibility.

    The registries are class-level state populated at import time by
    ``pyconfigre/loaders/__init__.py``.  Call :meth:`reset` in tests that
    register custom loaders to avoid cross-test pollution.

    Examples
    --------
    Auto-detect and load by file extension::

        ConfigLoader.detect_and_load("config.yaml")
        # → {'debug': True, 'port': 8000}

    Get a specific loader by name::

        yaml_loader = ConfigLoader.get_loader("yaml")
        config = yaml_loader("config.yaml")

    Register a custom loader::

        ConfigLoader.register_loader("ini", INILoader(), extensions=[".ini", ".cfg"])

    Validate an extension without loading::

        ConfigLoader.validate_extension(".yaml")   # → "yaml"
        ConfigLoader.validate_extension(".xyz")    # raises ValueError
    """

    # Registry: file extension → loader-type name
    _extension_registry: dict[str, str] = {}

    # Registry: loader-type name → loader instance
    _loader_registry: dict[str, BaseLoader] = {}

    # Snapshot taken after the built-in loaders are registered
    # set by loaders/__init__.py
    _builtin_snapshot: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------

    @classmethod
    def detect_and_load(cls, path: str | Path) -> dict[str, Any]:
        """
        Auto-detect file format from extension and load configuration.

        Parameters
        ----------
        path : str | Path
            Path to configuration file.

        Returns
        -------
        dict[str, Any]
            Loaded configuration dictionary.

        Raises
        ------
        ValueError
            If the file extension is not registered.  The extension is
            validated *before* checking whether the file exists so that
            unsupported-format errors surface immediately.
        ConfigLoadError
            If the file cannot be read or parsed.
        ConfigNotFoundError
            If the file does not exist (raised by the individual loader).

        Examples
        --------
        >>> config = ConfigLoader.detect_and_load("config.yaml")
        >>> config = ConfigLoader.detect_and_load("config.json")
        """
        file_path = Path(path)
        loader_type = cls.validate_extension(file_path.suffix)
        loader = cls.get_loader(loader_type)
        return loader(file_path)

    @classmethod
    def validate_extension(cls, extension: str) -> str:
        """
        Validate that *extension* is registered and return its loader-type name.

        Normalises the extension to lower-case and ensures it starts with a
        leading dot before looking it up.

        Parameters
        ----------
        extension : str
            File extension, e.g. ``".yaml"`` or ``"yaml"``.

        Returns
        -------
        str
            Registered loader-type name (e.g. ``"yaml"``).

        Raises
        ------
        ValueError
            If the extension is not registered.
        """
        normalised = extension.lower()
        if not normalised.startswith("."):
            normalised = f".{normalised}"

        if normalised not in cls._extension_registry:
            supported = ", ".join(sorted(cls._extension_registry))
            raise ValueError(
                f"Unsupported file format: '{extension}'. "
                f"Supported extensions: {supported}"
            )
        return cls._extension_registry[normalised]

    @classmethod
    def get_loader(cls, loader_type: str) -> BaseLoader:
        """
        Return a registered loader instance by type name.

        Parameters
        ----------
        loader_type : str
            Loader identifier, e.g. ``"yaml"``, ``"json"``, ``"env"``.

        Returns
        -------
        BaseLoader
            Loader instance.

        Raises
        ------
        ValueError
            If *loader_type* is not registered.
        """
        if loader_type not in cls._loader_registry:
            available = ", ".join(sorted(cls._loader_registry))
            raise ValueError(
                f"Unknown loader type: '{loader_type}'. Available loaders: {available}"
            )
        return cls._loader_registry[loader_type]

    @classmethod
    def register_loader(
        cls,
        loader_type: str,
        loader: BaseLoader,
        extensions: list[str] | None = None,
    ) -> None:
        """
        Register a loader instance under *loader_type*.

        Optionally maps file extensions to this loader for auto-detection.

        Parameters
        ----------
        loader_type : str
            Unique identifier for the loader (e.g. ``"yaml"``, ``"ini"``).
        loader : BaseLoader
            Loader instance.  Must be a subclass of :class:`BaseLoader`.
        extensions : list[str] | None, optional
            File extensions to associate with this loader
            (e.g. ``[".ini", ".cfg"]``).  Leading dots are added if absent.

        Raises
        ------
        TypeError
            If *loader* is not a :class:`BaseLoader` instance.

        Examples
        --------
        >>> ConfigLoader.register_loader("ini", INILoader(), extensions=[".ini"])
        """
        if not isinstance(loader, BaseLoader):
            raise TypeError(
                f"Loader must be a BaseLoader instance, got {type(loader).__name__!r}."
            )

        cls._loader_registry[loader_type] = loader

        for ext in extensions or []:
            normalised = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            cls._extension_registry[normalised] = loader_type

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @classmethod
    def list_loaders(cls) -> list[str]:
        """Return names of all registered loaders."""
        return sorted(cls._loader_registry)

    @classmethod
    def list_extensions(cls) -> dict[str, str]:
        """Return a mapping of registered extensions → loader-type names."""
        return dict(sorted(cls._extension_registry.items()))

    # ------------------------------------------------------------------
    # Test / reset support
    # ------------------------------------------------------------------

    @classmethod
    def _save_builtin_snapshot(cls) -> None:
        """
        Persist a snapshot of the registries after built-in loaders have been
        registered.  Called once by ``loaders/__init__.py``.  Subsequent calls
        are no-ops so that accidental double-import does not corrupt the snapshot.
        """
        if cls._builtin_snapshot is None:
            cls._builtin_snapshot = {
                "extensions": copy.copy(cls._extension_registry),
                "loaders": copy.copy(cls._loader_registry),
            }

    @classmethod
    def reset(cls) -> None:
        """
        Restore the registries to the state they were in immediately after the
        built-in loaders were registered.

        Intended for test teardown so that tests registering custom loaders do
        not pollute one another.

        Raises
        ------
        RuntimeError
            If called before the built-in loaders have been registered (i.e.
            before ``pyconfigre`` has been imported at least once).

        Examples
        --------
        ::

            def teardown():
                ConfigLoader.reset()
        """
        if cls._builtin_snapshot is None:
            raise RuntimeError(
                "ConfigLoader.reset() called before built-in loaders were "
                "registered.  Import 'pyconfigre' at least once first."
            )
        cls._extension_registry = copy.copy(cls._builtin_snapshot["extensions"])
        cls._loader_registry = copy.copy(cls._builtin_snapshot["loaders"])
