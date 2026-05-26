"""Base loader class defining the common interface for all configuration loaders."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..exceptions import ConfigNotFoundError, ConfigValidationError


class BaseLoader(ABC):
    """
    Abstract base class for all configuration loaders.

    Defines the interface and common functionality for loading configuration
    from different sources. Subclasses should implement the `__call__()` method
    with specific logic for their source type.

    All loaders are designed to be callable instances, allowing both:
    - Instantiation: `loader = JSONLoader(); config = loader(...)`
    - Direct usage: `config = JSONLoader()(...)`

    Loaders are typically used as singletons for convenience, but new instances
    can be created for fresh state if needed.
    """

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Load configuration.

        Returns
        -------
        dict[str, Any]
            Dictionary containing configuration data.

        Raises
        ------
        ConfigNotFoundError
            If loading or parsing fails.
        """
        raise NotImplementedError("Subclasses must implement __call__ method")

    def _validate_dict(self, data: Any) -> dict[str, Any]:
        """
        Validate that data is a dictionary, return empty dict if not.

        This common logic is used by all loaders to ensure consistent behavior.

        Parameters
        ----------
        data : Any
            Data to validate.

        Returns
        -------
        dict[str, Any]
            The data if it's a dict, otherwise an empty dict.

        Raises
        ------
        ConfigValidationError
            If data is not a dictionary.
        """
        if data is not None:
            if isinstance(data, dict):
                return data
            raise ConfigValidationError("Loaded configuration is not a dictionary")
        return {}

    def _check_file_exists(self, path: str | Path) -> Path:
        """
        Check if file exists and return as Path object.

        Common file checking logic used by file-based loaders.

        Parameters
        ----------
        path : str | Path
            Path to file.

        Returns
        -------
        Path
            Path object if file exists.

        Raises
        ------
        ConfigLoadError
            If file doesn't exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigNotFoundError(f"File not found: {path}")
        return file_path
