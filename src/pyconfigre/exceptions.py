"""Exception classes for pyconfig."""


class ConfigError(Exception):
    """
    Base exception for all configuration errors.

    All configuration-related exceptions inherit from this class,
    making it easy to catch configuration errors broadly.
    """

    pass


class ConfigLoadError(ConfigError):
    """
    Raised when configuration cannot be loaded from a source.

    This error occurs when file reading, parsing, or format-specific
    operations fail during configuration loading.
    """

    pass


class ConfigValidationError(ConfigError):
    """
    Raised when configuration fails validation.

    This error occurs when configuration data does not meet validation
    requirements (e.g., not a dictionary, missing required fields).
    """

    pass


class ConfigNotFoundError(ConfigError):
    """
    Raised when a configuration file is not found.

    This error occurs when the specified configuration file path
    does not exist or cannot be accessed.
    """

    pass
