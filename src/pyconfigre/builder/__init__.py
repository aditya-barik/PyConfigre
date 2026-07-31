"""
Builder package — fluent API builders for configuration management.

This package provides:

- :class:`RawConfigBuilder` — the pure pipeline (loading, merging, priority).
  No schema required.  Terminal method: :meth:`~RawConfigBuilder.build_dict`.
- :class:`ConfigBuilder` — extends :class:`RawConfigBuilder` with typed Pydantic
  validation.  Terminal method: :meth:`~ConfigBuilder.build`.

The internal :func:`_deep_merge` helper is re-exported here for backward
compatibility with code that imports ``from pyconfigre.builder import _deep_merge``.
"""

from ._merge import _deep_merge
from .config_builder import ConfigBuilder
from .raw_builder import RawConfigBuilder

__all__ = [
    "ConfigBuilder",
    "RawConfigBuilder",
    "_deep_merge",
]
