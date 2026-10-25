"""
Schema inference — generate Pydantic BaseModel source code from a config dict.

Provides :func:`infer_schema` which takes a loaded dictionary and produces
valid Python source code for a Pydantic ``BaseModel`` class hierarchy.

Examples
--------
::

    from pyconfigre.schema import infer_schema

    raw = {"debug": False, "port": 8080, "database": {"host": "localhost"}}
    print(infer_schema(raw, name="AppConfig"))
"""

from pathlib import Path
from typing import Any


def infer_schema(
    data: dict[str, Any],
    name: str = "GeneratedConfig",
    *,
    output_file: str | Path | None = None,
) -> str:
    """
    Generate Pydantic BaseModel source code from a configuration dictionary.

    Nested dicts become nested ``BaseModel`` subclasses.  The output is a
    string of valid Python that can be printed, written to a file, or
    compiled for quick prototyping.

    Parameters
    ----------
    data : dict[str, Any]
        Configuration dictionary to infer types from.
    name : str, optional
        Name for the root model class.  Default is ``"GeneratedConfig"``.
    output_file : str | Path | None, optional
        If provided, write the generated source to this file path.

    Returns
    -------
    str
        Valid Python source code defining Pydantic BaseModel classes.
    """
    submodels: list[str] = []
    root_lines = _generate_model(name, data, submodels)

    header = ["from pydantic import BaseModel", "from typing import Any", ""]
    source = "\n".join(header + submodels + root_lines) + "\n"

    if output_file:
        Path(output_file).write_text(source, encoding="utf-8")

    return source


def _infer_type(value: Any, key: str, submodels: list[str]) -> str:
    """Infer the Pydantic type string for a single value.

    Parameters
    ----------
    value : Any
        The configuration value.
    key : str
        The key name (used to derive nested class names).
    submodels : list[str]
        Accumulator for nested model source lines.

    Returns
    -------
    str
        A type annotation string.
    """
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        class_name = _to_class_name(key)
        sub_lines = _generate_model(class_name, value, submodels)
        submodels.extend(sub_lines + [""])
        return class_name
    if isinstance(value, list):
        if not value:
            return "list[Any]"
        first_type = _infer_type(value[0], key, submodels)
        if all(type(v) is type(value[0]) for v in value):
            return f"list[{first_type}]"
        return "list[Any]"
    if value is None:
        return "Any"
    return "Any"


def _to_class_name(key: str) -> str:
    """Convert a snake_case key to a PascalCase class name."""
    return "".join(part.capitalize() for part in key.split("_")) + "Config"


def _generate_model(
    name: str, data: dict[str, Any], submodels: list[str]
) -> list[str]:
    """Generate source lines for a single BaseModel class.

    Parameters
    ----------
    name : str
        Class name.
    data : dict[str, Any]
        Field data.
    submodels : list[str]
        Accumulator for nested model source lines.

    Returns
    -------
    list[str]
        Source code lines for this model.
    """
    lines = [f"class {name}(BaseModel):"]
    if not data:
        lines.append("    pass")
        return lines
    for key, value in data.items():
        safe_key = _sanitize_identifier(key)
        type_str = _infer_type(value, key, submodels)
        lines.append(f"    {safe_key}: {type_str} = {value!r}")
    return lines


def _sanitize_identifier(key: str) -> str:
    """Ensure a key is a valid Python identifier.

    Parameters
    ----------
    key : str
        Raw key from the config dict.

    Returns
    -------
    str
        A valid Python identifier.
    """
    result = ""
    for ch in key:
        if ch.isalnum() or ch == "_":
            result += ch
        else:
            result += "_"
    if result and result[0].isdigit():
        result = "_" + result
    if not result:
        result = "_field"
    return result
