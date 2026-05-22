"""
Fluent API builders for configuration management.

This module provides two public classes:

- :class:`RawConfigBuilder` — the pure pipeline (loading, merging, priority).
  No schema required.  Terminal method: :meth:`~RawConfigBuilder.build_dict`.
- :class:`ConfigBuilder` — extends :class:`RawConfigBuilder` with typed Pydantic
  validation.  Terminal method: :meth:`~ConfigBuilder.build`.
"""

import warnings
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError
from typing_extensions import Self

from .exceptions import ConfigLoadError, ConfigNotFoundError, ConfigValidationError
from .loaders import ConfigLoader

T = TypeVar("T", bound=BaseModel)


# ======================================================================
# RawConfigBuilder — schema-free pipeline
# ======================================================================


class RawConfigBuilder:
    """
    Schema-free configuration pipeline — loading, merging, and priority.

    Sources are merged in the order they are added — later sources take
    priority over earlier ones.  Nested dicts are merged recursively; all
    other types (including lists) are replaced wholesale.

    Priority (lowest → highest)
    ---------------------------
    ``from_file`` → ``from_env`` → ``from_dict`` → ``set``

    Use :meth:`build_dict` to obtain the final merged dictionary, or
    :meth:`peek` to inspect the state mid-chain without finalising.

    Examples
    --------
    Schmea-less usage::

        from pyconfigr import RawConfigBuilder

        raw_config = (
            RawConfigBuilder()
            .from_file("config.yaml")
            .from_env("MYAPP_")
            .build_dict()
        )

    Inspect assembled data mid-chain::

        builder = RawConfigBuilder().from_file("app.yaml").from_env("MYAPP_")
        print(builder.peek())   # plain dict — pipeline not finalised
        config = builder.build_dict()
    """

    def __init__(self) -> None:
        """Initialise an empty pipeline with no sources."""
        self._data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Source methods
    # ------------------------------------------------------------------

    def from_file(self, path: str | Path, optional: bool = False) -> Self:
        """
        Load configuration from a file, auto-detecting the format.

        The format is inferred from the file extension **before** checking
        whether the file exists, so an unsupported extension is reported
        immediately rather than after the file is created.

        Supported extensions: ``.yaml``, ``.yml``, ``.json``, ``.toml``
        (and any extension registered via
        :meth:`~pyconfigr.loaders.ConfigLoader.register_loader`).

        Parameters
        ----------
        path : str | Path
            Path to the configuration file.
        optional : bool, optional
            When ``True``, a missing file is silently ignored instead of
            raising :exc:`~pyconfigr.exceptions.ConfigNotFoundError`.
            Default is ``False``.

        Returns
        -------
        Self
            ``self``, for method chaining.

        Raises
        ------
        ValueError
            If the file extension is not supported.
        ConfigNotFoundError
            If the file does not exist and *optional* is ``False``.
        ConfigLoadError
            If the file cannot be read or parsed.

        Examples
        --------
        ::

            raw_config = (
                RawConfigBuilder()
                .from_file("config.yaml")
                .from_file("local.yaml", optional=True)
                .build_dict()
            )
        """
        path = Path(path)

        # Validate the extension first — gives a clear error even if the file
        # does not yet exist, which is the common case during development.
        ConfigLoader.validate_extension(path.suffix)

        if not path.exists():
            if optional:
                return self
            raise ConfigNotFoundError(f"Configuration file not found: {path}")

        try:
            data = ConfigLoader.detect_and_load(path)
            self._merge(data)
        except (ConfigLoadError, ConfigNotFoundError):
            raise
        except Exception as e:
            raise ConfigLoadError(
                f"Failed to load configuration from '{path}': {e}"
            ) from e

        return self

    def from_env(
        self,
        prefix: str = "",
        *,
        lowercase: bool = True,
        strip_prefix: bool = True,
        nested: bool = True,
    ) -> Self:
        """
        Load configuration from environment variables.

        By default, double underscores (``__``) in variable names after
        the prefix is stripped are interpreted as nested-key separators::

            MYAPP__DATABASE__HOST=localhost  →  {"database": {"host": "localhost"}}

        Single underscores are kept verbatim, so ``MYAPP_LOG_LEVEL=info``
        becomes ``{"log_level": "info"}``.

        Parameters
        ----------
        prefix : str, optional
            Only load variables whose names start with this string.
            Default is ``""`` (all variables).
        lowercase : bool, optional
            Keyword-only.  Convert keys to lower-case after stripping the
            prefix.  Default is ``True``.
        strip_prefix : bool, optional
            Keyword-only.  Remove *prefix* from each key before storing it.
            Default is ``True``.
        nested : bool, optional
            Keyword-only.  Expand ``__``-separated keys into nested dicts.
            Default is ``True``.  Pass ``False`` to keep keys flat when
            double underscores are intentional parts of a key name.

        Returns
        -------
        Self
            ``self``, for method chaining.

        Examples
        --------
        Flat variables::

            # MYAPP_DEBUG=true  MYAPP_PORT=8000
            RawConfigBuilder().from_env("MYAPP_").build_dict()
            # → {"debug": True, "port": 8000}

        Nested variables::

            # MYAPP__DATABASE__HOST=localhost  MYAPP__DATABASE__PORT=5432
            RawConfigBuilder().from_env("MYAPP__").build_dict()
            # → {"database": {"host": "localhost", "port": 5432}}

        Opt out of nesting::

            RawConfigBuilder().from_env("MYAPP__", nested=False).build_dict()
            # Keys with __ are kept flat: {"database__host": "localhost"}
        """
        loader = ConfigLoader.get_loader("env")
        data = loader(
            prefix=prefix,
            lowercase=lowercase,
            strip_prefix=strip_prefix,
            nested=nested,
        )
        self._merge(data)
        return self

    def from_dict(self, data: dict[str, Any]) -> Self:
        """
        Merge a plain dictionary into the configuration.

        Parameters
        ----------
        data : dict[str, Any]
            Configuration values to merge.  Nested dicts are deep-merged;
            all other types replace existing values.

        Returns
        -------
        Self
            ``self``, for method chaining.

        Examples
        --------
        ::

            raw_config = (
                RawConfigBuilder()
                .from_dict({"debug": True, "port": 3000})
                .build_dict()
            )
        """
        self._merge(data)
        return self

    def set(self, key: str, value: Any) -> Self:
        """
        Set a single configuration value, optionally using dot notation.

        Parameters
        ----------
        key : str
            Key name.  Use dots to address nested keys:
            ``"server.port"`` sets ``{"server": {"port": value}}``.
        value : Any
            Value to assign.

        Returns
        -------
        Self
            ``self``, for method chaining.

        Raises
        ------
        TypeError
            If a dot-notation segment traverses an existing value that is
            not a dict (e.g. ``set("db.host", …)`` when ``db`` is already
            set to a string).

        Examples
        --------
        ::

            raw_config = (
                RawConfigBuilder()
                .set("debug", True)
                .set("server.port", 8080)
                .build_dict()
            )
        """
        if "." not in key:
            self._data[key] = value
            return self

        keys = key.split(".")
        current = self._data
        for depth, segment in enumerate(keys[:-1]):
            if segment not in current:
                current[segment] = {}
            node = current[segment]
            if not isinstance(node, dict):
                path_so_far = ".".join(keys[: depth + 1])
                raise TypeError(
                    f"Cannot set '{key}': '{path_so_far}' is already set to a "
                    f"{type(node).__name__!r} value, not a dict.  "
                    f"Call from_dict({{{path_so_far!r}: {{…}}}})) to replace it first."
                )
            current = node
        current[keys[-1]] = value
        return self

    # ------------------------------------------------------------------
    # Terminal / Inspection methods
    # ------------------------------------------------------------------

    def build_dict(self) -> dict[str, Any]:
        """
        Return the final merged configuration as a plain dictionary.

        This is the terminal method for schema-free pipelines.  It returns
        a shallow copy of the assembled data, equivalent to calling
        :meth:`peek` but signalling intent that the pipeline is complete.

        Returns
        -------
        dict[str, Any]
            The assembled configuration dictionary.

        Examples
        --------
        ::

            raw_config = (
                RawConfigBuilder()
                .from_file("config.yaml")
                .from_env("MYAPP_")
                .build_dict()
            )
        """
        return dict(self._data)

    def peek(self) -> dict[str, Any]:
        """
        Return a copy of the current merged data without finalising.

        Useful for debugging mid-chain to inspect what has been assembled
        so far.

        Returns
        -------
        dict[str, Any]
            Snapshot of the current configuration state.

        Examples
        --------
        ::

            builder = RawConfigBuilder().from_file("app.yaml")
            print(builder.peek())   # {'debug': False, 'port': 8000}
            config = builder.from_env("MYAPP_").build_dict()
        """
        return dict(self._data)

    # kept for backwards compatibility — peek() is the preferred name
    def get_raw_data(self) -> dict[str, Any]:
        """Return assembled data without validation.

        .. deprecated:: 0.1.1
            :meth:`get_raw_data` is deprecated and will be removed in a future
            release.  Use :meth:`peek` instead — it is identical in behaviour::

                # Before
                builder.get_raw_data()

                # After
                builder.peek()
        """
        warnings.warn(
            "get_raw_data() is deprecated and will be removed in a future release. "
            "Use peek() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.peek()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _merge(self, new_data: dict[str, Any]) -> None:
        """Deep-merge *new_data* into the current state. Later wins."""
        _deep_merge(self._data, new_data)


class ConfigBuilder(RawConfigBuilder, Generic[T]):
    """
    Fluent API builder for loading, merging, and validating configuration.

    Extends :class:`RawConfigBuilder` with typed Pydantic validation.
    All pipeline methods (:meth:`from_file`, :meth:`from_env`,
    :meth:`from_dict`, :meth:`set`, :meth:`peek`) are inherited.  Use
    :meth:`build` to validate and return a typed Pydantic model instance.

    Parameters
    ----------
    config_class : type[T]
        Pydantic ``BaseModel`` subclass used to validate the final
        assembled configuration when :meth:`build` is called.

    Examples
    --------
    Basic usage::

        from pydantic import BaseModel
        from pyconfigr import ConfigBuilder

        class AppConfig(BaseModel):
            debug: bool = False
            port: int = 8000

        config = (
            ConfigBuilder(AppConfig)
            .from_file("config.yaml")
            .from_env("MYAPP_")
            .build()
        )

    Multiple sources with explicit priority::

        config = (
            ConfigBuilder(AppConfig)
            .from_file("base.yaml")          # lowest priority
            .from_file("overrides.json", optional=True)
            .from_env("MYAPP_")
            .from_dict({"debug": True})      # highest priority
            .build()
        )
    """

    def __init__(self, config_class: type[T]) -> None:
        """
        Initialise the builder with a Pydantic schema class.

        Parameters
        ----------
        config_class : type[T]
            Pydantic ``BaseModel`` subclass used to validate the assembled
            configuration when :meth:`build` is called.  Stored internally
            as the private attribute ``_config_class``.
        """
        self._config_class = config_class
        self._data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Terminal method
    # ------------------------------------------------------------------

    def build(self) -> T:
        """
        Validate and return the assembled configuration object.

        Returns
        -------
        T
            An instance of the schema class passed to :meth:`__init__`,
            populated with the assembled data and validated by Pydantic.

        Raises
        ------
        ConfigValidationError
            If the assembled data fails Pydantic validation.

        Examples
        --------
        ::

            config = ConfigBuilder(AppConfig).from_file("app.yaml").build()
            print(config.port)
        """
        try:
            return self._config_class.model_validate(self._data)
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration validation failed for "
                f"'{self._config_class.__name__}': {e}"
            ) from e


# ------------------------------------------------------------------
# Module-level merge helper (shared by RawConfigBuilder and ConfigBuilder)
# ------------------------------------------------------------------


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    """
    Recursively merge *source* into *target* in-place.

    Rules
    -----
    - ``dict`` + ``dict``  →  recursively merged (target keys not in source
      are preserved).
    - anything else        →  source value replaces target value entirely.
    - **Lists are replaced**, not extended.  This is intentional: a list
      in a config file represents a complete value (e.g. ``allowed_hosts``),
      not a partial one to be appended to.

    Parameters
    ----------
    target : dict[str, Any]
        Dictionary modified in-place.
    source : dict[str, Any]
        Dictionary whose values take priority.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
