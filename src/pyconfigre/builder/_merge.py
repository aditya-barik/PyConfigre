"""
Deep-merge utility shared by all builder classes.

This module is internal (prefixed with ``_``).  The function is re-exported
from :mod:`pyconfigre.builder` for backward compatibility.
"""

from typing import Any


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
