"""
Field validation helpers shared by all builder classes.

This module is internal (prefixed with ``_``).  The functions are used by
:class:`RawConfigBuilder`, :class:`DataClassConfigBuilder`, and
:class:`ConfigBuilder` to enforce ``unknown_fields`` and ``missing_fields``
modes at build time.
"""

import warnings

from ..exceptions import ConfigValidationError


def _handle_unknown(
    extra: set[str], mode: str, context: str = ""
) -> None:
    """Handle unknown (extra) fields according to *mode*.

    Parameters
    ----------
    extra : set[str]
        Field names present in data but not in the expected set.
    mode : str
        One of ``"ignore"``, ``"warn"``, ``"forbid"``.
    context : str, optional
        Additional context appended to the message.
    """
    msg = f"Unknown fields{context}: {sorted(extra)}"
    if mode == "forbid":
        raise ConfigValidationError(msg)
    if mode == "warn":
        warnings.warn(msg, UserWarning, stacklevel=3)


def _handle_missing(
    missing: set[str], mode: str, context: str = ""
) -> None:
    """Handle missing required fields according to *mode*.

    Parameters
    ----------
    missing : set[str]
        Field names required but absent from data.
    mode : str
        One of ``"ignore"``, ``"warn"``, ``"forbid"``.
    context : str, optional
        Additional context appended to the message.
    """
    msg = f"Missing required fields{context}: {sorted(missing)}"
    if mode == "forbid":
        raise ConfigValidationError(msg)
    if mode == "warn":
        warnings.warn(msg, UserWarning, stacklevel=3)
