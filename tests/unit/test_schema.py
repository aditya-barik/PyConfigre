"""Test suite for pyconfigre.schema — schema inference.

Covers flat dicts, nested subclass creation, type inference ordering,
None handling, list inference, compilable output, and file writing.
"""

from pathlib import Path

from pyconfigre.schema import infer_schema


class TestInferSchema:
    """Tests for infer_schema()."""

    def test_flat_dict(self) -> None:
        """Flat dict produces a single BaseModel class."""
        source = infer_schema({"host": "localhost", "port": 8080})
        assert "class GeneratedConfig(BaseModel):" in source
        assert "host: str" in source
        assert "port: int" in source

    def test_nested_subclass_creation(self) -> None:
        """Nested dicts produce nested BaseModel subclasses."""
        source = infer_schema(
            {"database": {"host": "localhost", "port": 5432}},
            name="AppConfig",
        )
        assert "class DatabaseConfig(BaseModel):" in source
        assert "class AppConfig(BaseModel):" in source
        assert "database: DatabaseConfig" in source

    def test_bool_before_int_ordering(self) -> None:
        """bool values are inferred as bool, not int."""
        source = infer_schema({"debug": True})
        assert "debug: bool" in source
        assert "debug: int" not in source

    def test_none_becomes_any(self) -> None:
        """None values are inferred as Any."""
        source = infer_schema({"optional_val": None})
        assert "optional_val: Any" in source

    def test_list_element_type_inference(self) -> None:
        """Homogeneous lists infer element type."""
        source = infer_schema({"ports": [80, 443, 8080]})
        assert "ports: list[int]" in source

    def test_mixed_type_list_becomes_list_any(self) -> None:
        """Mixed-type lists become list[Any]."""
        source = infer_schema({"items": [1, "two", 3.0]})
        assert "items: list[Any]" in source

    def test_empty_list_becomes_list_any(self) -> None:
        """Empty lists become list[Any]."""
        source = infer_schema({"empty": []})
        assert "empty: list[Any]" in source

    def test_valid_python_output(self) -> None:
        """Generated source code compiles without errors."""
        source = infer_schema(
            {
                "debug": False,
                "port": 8080,
                "ratio": 3.14,
                "name": "app",
                "database": {"host": "localhost", "port": 5432},
                "tags": ["web", "api"],
                "counts": [1, 2, 3],
                "mixed": [1, "a"],
                "empty_list": [],
                "nullable": None,
            },
            name="FullConfig",
        )
        compile(source, "<test>", "exec")

    def test_output_file_writes(self, temp_dir: Path) -> None:
        """output_file parameter writes to disk."""
        out = temp_dir / "schema.py"
        source = infer_schema(
            {"key": "value"}, name="FileConfig", output_file=out
        )
        assert out.exists()
        assert out.read_text(encoding="utf-8") == source

    def test_custom_name(self) -> None:
        """Custom root class name is used."""
        source = infer_schema({"x": 1}, name="MyConfig")
        assert "class MyConfig(BaseModel):" in source

    def test_empty_dict(self) -> None:
        """Empty dict produces a pass-only class."""
        source = infer_schema({}, name="EmptyConfig")
        assert "class EmptyConfig(BaseModel):" in source
        assert "    pass" in source

    def test_float_inference(self) -> None:
        """Float values inferred as float."""
        source = infer_schema({"ratio": 3.14})
        assert "ratio: float" in source

    def test_sanitize_identifier_special_chars(self) -> None:
        """Keys with special characters are sanitised."""
        source = infer_schema({"my-key": "val", "123start": 1})
        assert "my_key: str" in source
        assert "_123start: int" in source

    def test_unknown_type_becomes_any(self) -> None:
        """Unsupported types (e.g. set) fall back to Any."""
        source = infer_schema({"tags": {1, 2, 3}})
        assert "tags: Any" in source

    def test_sanitize_empty_key(self) -> None:
        """A key that becomes empty after sanitisation gets '_field'."""
        from pyconfigre.schema import _sanitize_identifier

        assert _sanitize_identifier("") == "_field"
