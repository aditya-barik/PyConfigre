"""Configuration loaders for different file formats and sources."""

from .base import BaseLoader
from .env import ENVLoader
from .json import JSONLoader
from .manager import ConfigLoader
from .toml import TOMLLoader
from .yaml import YAMLLoader

# Singleton instances for convenient direct usage
yaml_loader = YAMLLoader()
json_loader = JSONLoader()
toml_loader = TOMLLoader()
env_loader = ENVLoader()

# Register all built-in loaders.
# Order matters only for list_loaders() output — functionality is identical.
ConfigLoader.register_loader("yaml", yaml_loader, extensions=[".yaml", ".yml"])
ConfigLoader.register_loader("json", json_loader, extensions=[".json"])
ConfigLoader.register_loader("toml", toml_loader, extensions=[".toml"])
ConfigLoader.register_loader("env", env_loader)

# Persist a snapshot of the registries so ConfigLoader.reset() can restore
# them to this exact state in tests that add custom loaders.
ConfigLoader._save_builtin_snapshot()

__all__ = [
    # Base class
    "BaseLoader",
    # Loader classes
    "YAMLLoader",
    "JSONLoader",
    "TOMLLoader",
    "ENVLoader",
    # Loader manager
    "ConfigLoader",
    # Singleton instances for convenience
    "yaml_loader",
    "json_loader",
    "toml_loader",
    "env_loader",
]
