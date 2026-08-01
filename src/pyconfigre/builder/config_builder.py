"""
Typed configuration builder with Pydantic validation.

Provides :class:`ConfigBuilder` — extends :class:`RawConfigBuilder` with
``Generic[T]`` and Pydantic ``model_validate`` on :meth:`build`.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from ..exceptions import ConfigValidationError
from .raw_builder import RawConfigBuilder

T = TypeVar("T", bound=BaseModel)


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
        from pyconfigre import ConfigBuilder

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
