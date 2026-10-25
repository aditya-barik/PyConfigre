"""
Condition helpers for conditional source loading.

Provides composable condition functions for use with the ``when=``
parameter on builder source methods.

Examples
--------
::

    from pyconfigre.conditions import env_is, env_in

    config = (
        ConfigBuilder(AppConfig)
        .from_file("base.yaml")
        .from_file("dev.yaml", when=env_is("ENV", "dev"))
        .from_env("MYAPP_", when=env_in("ENV", ["staging", "prod"]))
        .build()
    )
"""

import os
from collections.abc import Callable, Iterable
from typing import Any


def env_is(var: str, value: str) -> Callable[[], bool]:
    """Return a condition that is ``True`` when ``os.environ[var] == value``.

    Parameters
    ----------
    var : str
        Environment variable name.
    value : str
        Expected value.

    Returns
    -------
    Callable[[], bool]
        A callable returning ``True`` when the variable matches.
    """
    return lambda: os.environ.get(var) == value


def env_in(var: str, values: Iterable[str]) -> Callable[[], bool]:
    """Return a condition that is ``True`` when ``os.environ[var]`` is in *values*.

    Parameters
    ----------
    var : str
        Environment variable name.
    values : Iterable[str]
        Accepted values.

    Returns
    -------
    Callable[[], bool]
        A callable returning ``True`` when the variable is in the set.
    """
    values_set = frozenset(values)
    return lambda: os.environ.get(var) in values_set


def when_all(*conditions: Any) -> Callable[[], bool]:
    """Return a condition that is ``True`` when all sub-conditions are ``True``.

    Parameters
    ----------
    *conditions : callable | tuple
        Each element is a condition (callable or 2-tuple).

    Returns
    -------
    Callable[[], bool]
        Composite condition.
    """
    evaluated = [_make_callable(c) for c in conditions]
    return lambda: all(fn() for fn in evaluated)


def when_any(*conditions: Any) -> Callable[[], bool]:
    """Return a condition that is ``True`` when any sub-condition is ``True``.

    Parameters
    ----------
    *conditions : callable | tuple
        Each element is a condition (callable or 2-tuple).

    Returns
    -------
    Callable[[], bool]
        Composite condition.
    """
    evaluated = [_make_callable(c) for c in conditions]
    return lambda: any(fn() for fn in evaluated)


def _make_callable(condition: Any) -> Callable[[], bool]:
    """Normalize a condition to a callable.

    Parameters
    ----------
    condition : callable | tuple
        A callable returning bool, or a 2-tuple ``(env_var, value)``
        which is shorthand for :func:`env_is`.

    Returns
    -------
    Callable[[], bool]
        The normalised callable.

    Raises
    ------
    TypeError
        If *condition* is not callable or a 2-tuple.
    """
    if callable(condition):
        return condition  # type: ignore[no-any-return]
    if isinstance(condition, tuple) and len(condition) == 2:
        var, value = condition
        return env_is(var, value)
    raise TypeError(
        f"Condition must be a callable or a 2-tuple (env_var, value), "
        f"got {type(condition).__name__}: {condition!r}"
    )


def _evaluate_condition(condition: Any) -> bool:
    """Evaluate a condition value to a bool.

    Parameters
    ----------
    condition : callable | tuple
        A condition to evaluate.

    Returns
    -------
    bool
        The result of the condition.
    """
    return _make_callable(condition)()
