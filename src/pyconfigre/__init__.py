"""
PyConfigre — configuration assembly pipeline for Python.

Load from any source, merge with priority, validate with Pydantic — or
consume as a plain dict.  Built for teams who want explicit, readable,
testable configuration code.

Examples
--------
Schema-less usage (no Pydantic needed)::

    from pyconfigre import RawConfigBuilder

    raw_config = (
        RawConfigBuilder()
        .from_file("config.yaml")
        .from_env("MYAPP_")
        .build_dict()
    )

Typed usage with Pydantic validation::

    from pydantic import BaseModel
    from pyconfigre import ConfigBuilder

    class AppConfig(BaseModel):
        debug: bool = False
        port: int = 8000
        database_url: str

    config = (
        ConfigBuilder(AppConfig)
        .from_file("config.yaml")
        .from_env("MYAPP_")
        .build()
    )

Multiple sources (lowest → highest priority)::

    config = (
        ConfigBuilder(AppConfig)
        .from_file("base.yaml")
        .from_file("overrides.json", optional=True)
        .from_env("MYAPP__")
        .from_dict({"debug": True})
        .build()
    )

Inspect assembled data before validating::

    builder = ConfigBuilder(AppConfig).from_file("app.yaml").from_env("MYAPP_")
    print(builder.peek())   # plain dict — no validation yet
    config = builder.build()
"""

from importlib.metadata import PackageNotFoundError, version

from .builder import ConfigBuilder, RawConfigBuilder
from .exceptions import (
    ConfigError,
    ConfigLoadError,
    ConfigNotFoundError,
    ConfigValidationError,
)

try:
    __version__ = version("pyconfigre")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.2.0.dev0"

__all__ = [
    "ConfigBuilder",
    "RawConfigBuilder",
    "ConfigError",
    "ConfigLoadError",
    "ConfigNotFoundError",
    "ConfigValidationError",
]
