"""Environment variable configuration loader."""

import os
from typing import Any

from .base import BaseLoader


class ENVLoader(BaseLoader):
    """
    Load configuration from environment variables.

    Provides flexible filtering by prefix, optional key normalisation,
    and intelligent value parsing (booleans, numbers, None, strings).

    Double underscores (``__``) in variable names are interpreted as
    nested-key separators, producing nested dicts.  Single underscores
    are kept as-is so they remain part of the key name.

    Examples
    --------
    Simple flat variables::

        # MYAPP_DEBUG=true  MYAPP_PORT=8000
        loader = ENVLoader()
        loader(prefix="MYAPP_")
        # → {'debug': True, 'port': 8000}

    Nested variables via double underscore::

        # MYAPP__DATABASE__HOST=localhost  MYAPP__DATABASE__PORT=5432
        loader(prefix="MYAPP__")
        # → {'database': {'host': 'localhost', 'port': 5432}}

    Mixed nesting::

        # APP__SERVER__HOST=0.0.0.0  APP__SERVER__PORT=8080  APP__DEBUG=false
        loader(prefix="APP__")
        # → {'server': {'host': '0.0.0.0', 'port': 8080}, 'debug': False}

    Without stripping prefix::

        loader(prefix="MYAPP_", strip_prefix=False)
        # → {'myapp_debug': True, 'myapp_port': 8000}
    """

    # Separator used to express nested keys in environment variable names.
    NESTING_SEPARATOR = "__"

    def __call__(
        self,
        prefix: str = "",
        lowercase: bool = True,
        strip_prefix: bool = True,
        nested: bool = True,
    ) -> dict[str, Any]:
        """
        Load configuration from environment variables.

        Parameters
        ----------
        prefix : str, optional
            Only load variables starting with this prefix (e.g. ``"MYAPP_"``
            for flat keys or ``"MYAPP__"`` for nested keys).
            Default is ``""`` (all variables).
        lowercase : bool, optional
            Convert keys to lowercase after stripping the prefix.
            Default is ``True``.
        strip_prefix : bool, optional
            Remove *prefix* from the key before storing.
            Default is ``True``.
        nested : bool, optional
            Interpret double underscores (``__``) as nested-key separators,
            producing nested dicts.  Set to ``False`` to keep keys flat.
            Default is ``True``.

        Returns
        -------
        dict[str, Any]
            Configuration dict, potentially nested when *nested* is ``True``.

        Notes
        -----
        List merging is intentionally **not** supported via environment
        variables — lists must be supplied through file-based sources and
        overridden wholesale, not element-by-element.
        """
        flat: dict[str, Any] = {}

        for key, value in os.environ.items():
            # Filter by prefix if specified
            if prefix and not key.startswith(prefix):
                continue

            # Process the key
            config_key = key[len(prefix) :] if (strip_prefix and prefix) else key

            if lowercase:
                config_key = config_key.lower()

            # Parse value to appropriate Python type
            flat[config_key] = self._parse_value(value)

        if nested:
            return self._unflatten(flat)
        return flat

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _unflatten(flat: dict[str, Any]) -> dict[str, Any]:
        """
        Convert a flat dict with ``__``-separated keys into a nested dict.

        Single underscores are **not** treated as separators — they remain
        part of the key name.  Only consecutive double underscores trigger
        nesting.

        Parameters
        ----------
        flat : dict[str, Any]
            Flat dictionary whose keys may contain ``__`` separators.

        Returns
        -------
        dict[str, Any]
            Nested dictionary.

        Examples
        --------
        >>> ENVLoader._unflatten({"database__host": "localhost", "debug": True})
        {'database': {'host': 'localhost'}, 'debug': True}
        """
        result: dict[str, Any] = {}
        for key, value in flat.items():
            parts = key.split("__")
            current = result
            for part in parts[:-1]:
                # If an intermediate key already exists as a scalar, replace
                # it with a dict — this mirrors deep-merge "last wins" logic.
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result

    @staticmethod
    def _parse_value(value: str) -> Any:
        """
        Parse a string value from an environment variable to a Python type.

        Conversion order:

        1. Boolean  — ``"true"``, ``"yes"``, ``"1"``, ``"on"`` → ``True``
                       ``"false"``, ``"no"``, ``"0"``, ``"off"`` → ``False``
        2. None     — ``"null"``, ``"none"``, ``""`` → ``None``
        3. Integer  — ``"42"`` → ``42``
        4. Float    — ``"3.14"`` → ``3.14``
        5. String   — everything else is kept as-is.

        Parameters
        ----------
        value : str
            Raw string value from ``os.environ``.

        Returns
        -------
        Any
            Parsed Python value.
        """
        lower = value.lower()

        # Handle boolean
        if lower in ("true", "yes", "1", "on"):
            return True
        if lower in ("false", "no", "0", "off"):
            return False

        # Handle None
        if lower in ("null", "none", ""):
            return None

        # Try integer first — "42" must become 42, not 42.0
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value
