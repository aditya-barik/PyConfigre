"""
Typed configuration builder with Python dataclass instantiation.

Provides :class:`DataClassConfigBuilder` — extends :class:`RawConfigBuilder`
with ``Generic[D]`` and stdlib ``dataclasses`` instantiation on :meth:`build`.
No Pydantic dependency required.
"""

import dataclasses
import warnings
from typing import (
    Any,
    Generic,
    Literal,
    TypeGuard,
    TypeVar,
    cast,
    get_origin,
    get_type_hints,
)

from ..exceptions import ConfigValidationError
from .raw_builder import RawConfigBuilder

D = TypeVar("D")


def _is_concrete_type(tp: Any) -> TypeGuard[type]:
    """Return True if *tp* is a plain, non-parameterized class.

    In Python 3.10, parameterized generics such as ``list[str]`` are
    instances of :class:`type` (they are :class:`types.GenericAlias`
    objects, which is a subclass of :class:`type`).  Such aliases cannot
    be passed as the second argument to :func:`isinstance`, so we use
    :func:`typing.get_origin` to distinguish them from concrete classes.
    """
    return isinstance(tp, type) and get_origin(tp) is None


# Truthy / falsy string sets for bool coercion
_TRUTHY: frozenset[str] = frozenset({"true", "1", "yes"})
_FALSY: frozenset[str] = frozenset({"false", "0", "no"})

# Valid modes for handling fields present in the merged data but not in the dataclass
_UNKNOWN_FIELDS_MODES: frozenset[str] = frozenset({"ignore", "warn", "forbid"})


class DataClassConfigBuilder(RawConfigBuilder, Generic[D]):
    """
    Fluent API builder for loading, merging, and instantiating dataclasses.

    Extends :class:`RawConfigBuilder` with typed dataclass instantiation.
    All pipeline methods (:meth:`from_file`, :meth:`from_env`,
    :meth:`from_dict`, :meth:`set`, :meth:`peek`) are inherited.  Use
    :meth:`build` to instantiate and return a typed dataclass instance.

    Basic type coercion is performed for common cases where config files
    parse values as strings (e.g. ``"8080"`` → ``int(8080)``).

    Parameters
    ----------
    schema : type[D]
        A ``@dataclass``-decorated class used to instantiate the final
        assembled configuration when :meth:`build` is called.
    unknown_fields : {"ignore", "warn", "forbid"}, default "warn"
        How to handle keys in the merged config dict that are not dataclass
        fields.

        - ``"ignore"`` — silently drop extra keys.
        - ``"warn"`` — emit a ``UserWarning`` listing the ignored keys.
        - ``"forbid"`` — raise :exc:`ConfigValidationError` for extra keys.

    Raises
    ------
    TypeError
        If *schema* is not a dataclass.
    ValueError
        If *unknown_fields* is not one of the supported modes.

    Examples
    --------
    Basic usage::

        from dataclasses import dataclass
        from pyconfigre import DataClassConfigBuilder

        @dataclass
        class AppConfig:
            debug: bool = False
            port: int = 8080

        config = (
            DataClassConfigBuilder(AppConfig)
            .from_file("config.yaml")
            .from_env("MYAPP_")
            .build()
        )

    Nested dataclasses::

        @dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @dataclass
        class AppConfig:
            app_name: str = "my_app"
            database: DatabaseConfig = field(default_factory=DatabaseConfig)

        config = (
            DataClassConfigBuilder(AppConfig)
            .from_file("config.yaml")
            .build()
        )
        print(config.database.host)  # "localhost"
    """

    def __init__(
        self,
        schema: type[D],
        unknown_fields: Literal["ignore", "warn", "forbid"] = "warn",
    ) -> None:
        """
        Initialise the builder with a dataclass schema.

        Parameters
        ----------
        schema : type[D]
            A ``@dataclass``-decorated class.  Stored internally as the
            private attribute ``_schema``.
        unknown_fields : {"ignore", "warn", "forbid"}, default "warn"
            Controls how unexpected keys in the merged config data are handled.

        Raises
        ------
        TypeError
            If *schema* is not a dataclass.
        ValueError
            If *unknown_fields* is not one of "ignore", "warn", or "forbid".
        """
        if not dataclasses.is_dataclass(schema):
            raise TypeError(
                f"DataClassConfigBuilder requires a @dataclass class, "
                f"got {type(schema).__name__!r}: {schema!r}"
            )
        if unknown_fields not in _UNKNOWN_FIELDS_MODES:
            raise ValueError(
                f"unknown_fields must be one of {_UNKNOWN_FIELDS_MODES!r}, "
                f"got {unknown_fields!r}"
            )
        self._schema: type[D] = schema
        self._data: dict[str, Any] = {}
        self._unknown_fields: str = unknown_fields

    # ------------------------------------------------------------------
    # Terminal method
    # ------------------------------------------------------------------

    def build(self) -> D:
        """
        Instantiate and return the assembled configuration as a dataclass.

        Performs basic type coercion (str → int/float/bool) and recursive
        nested dataclass instantiation.  Extra keys in the merged dict that
        are not fields of the dataclass are handled according to the
        ``unknown_fields`` setting passed to :meth:`__init__`.

        Returns
        -------
        D
            An instance of the schema class passed to :meth:`__init__`,
            populated with the assembled data.

        Raises
        ------
        ConfigValidationError
            If a required field (no default) is missing from the assembled
            data, or if type coercion fails.

        Examples
        --------
        ::

            config = DataClassConfigBuilder(AppConfig).from_file("app.yaml").build()
            print(config.port)
        """
        try:
            return cast(
                D,
                _instantiate_dataclass(self._schema, self._data, self._unknown_fields),
            )
        except (TypeError, ValueError) as e:
            raise ConfigValidationError(
                f"Configuration validation failed for '{self._schema.__name__}': {e}"
            ) from e


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _coerce_value(value: Any, target_type: type) -> Any:
    """
    Coerce *value* to *target_type* for common config-file scenarios.

    Parameters
    ----------
    value : Any
        The raw value from the merged configuration dict.
    target_type : type
        The type annotation from the dataclass field.

    Returns
    -------
    Any
        The coerced value, or the original value if no coercion applies.
    """
    # Parameterized generics (e.g. list[str]) cannot be used as the
    # second argument to isinstance() on Python 3.10 and are not coercible
    # by this helper, so pass them through unchanged.
    if not _is_concrete_type(target_type):
        return value

    # Already correct type — fast path
    if isinstance(value, target_type):
        # bool is a subclass of int, so int fields with bool values
        # should NOT be short-circuited here
        if not (target_type is int and isinstance(value, bool)):
            return value

    if isinstance(value, str):
        if target_type is int:
            return int(value)
        if target_type is float:
            return float(value)
        if target_type is bool:
            lower = value.lower()
            if lower in _TRUTHY:
                return True
            if lower in _FALSY:
                return False
            raise ValueError(
                f"Cannot coerce {value!r} to bool. "
                f"Expected one of: {sorted(_TRUTHY | _FALSY)}"
            )

    # bool → int pass-through (bool is subclass of int)
    if target_type is int and isinstance(value, bool):
        return int(value)

    return value


def _instantiate_dataclass(
    dc_class: type, data: dict[str, Any], unknown_fields: str = "warn"
) -> Any:
    """
    Recursively instantiate a dataclass from a dictionary.

    Parameters
    ----------
    dc_class : type
        A ``@dataclass``-decorated class.
    data : dict[str, Any]
        Configuration data to populate the dataclass.
    unknown_fields : {"ignore", "warn", "forbid"}, default "warn"
        How to handle keys in *data* that are not fields of *dc_class*.

    Returns
    -------
    Any
        An instance of *dc_class*.

    Raises
    ------
    TypeError
        If a required field is missing and has no default value.
    ValueError
        If *unknown_fields* is ``"forbid"`` and extra keys are present.
    """
    hints = get_type_hints(dc_class)
    fields = dataclasses.fields(dc_class)
    field_names = {f.name for f in fields}

    extra_keys = [k for k in data if k not in field_names]
    if extra_keys:
        if unknown_fields == "forbid":
            raise ValueError(f"Unknown fields for {dc_class.__name__}: {extra_keys}")
        if unknown_fields == "warn":
            warnings.warn(
                f"Unknown fields for {dc_class.__name__} will be ignored: {extra_keys}",
                UserWarning,
                stacklevel=3,
            )

    kwargs: dict[str, Any] = {}
    for f in fields:
        if f.name not in data:
            # Let dataclass handle missing fields — it will raise TypeError
            # for fields without defaults
            continue

        value = data[f.name]
        field_type = hints[f.name]

        # Nested dataclass: dict → dataclass instance
        if (
            isinstance(value, dict)
            and _is_concrete_type(field_type)
            and dataclasses.is_dataclass(field_type)
        ):
            kwargs[f.name] = _instantiate_dataclass(field_type, value, unknown_fields)
        elif isinstance(field_type, type):
            kwargs[f.name] = _coerce_value(value, field_type)
        else:
            # Complex types (Optional, Union, etc.) — pass through
            kwargs[f.name] = value

    return dc_class(**kwargs)
