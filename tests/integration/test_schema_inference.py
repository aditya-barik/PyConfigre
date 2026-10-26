"""
Use case: generating Pydantic BaseModel source from configuration data.

Schema inference is a prototyping tool — users load a config file and generate
a starting-point Pydantic model.  These tests verify the end-to-end flow:
load real config data, infer the schema, and validate the generated output.
"""

import pytest

from pyconfigre import RawConfigBuilder, infer_schema


@pytest.mark.integration
class TestSchemaInference:
    """End-to-end schema inference from real config data."""

    def test_infer_from_flat_yaml(self, cfg_dir):
        """Infer schema from a flat YAML config loaded through the builder."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: myapp\ndebug: false\nport: 8080\n")

        data = RawConfigBuilder().from_file(f).build_dict()
        source = infer_schema(data, name="AppConfig")

        assert "class AppConfig(BaseModel):" in source
        assert "name: str" in source
        assert "debug: bool" in source
        assert "port: int" in source

    def test_infer_from_nested_config(self, cfg_dir):
        """Nested dicts produce nested BaseModel subclasses."""
        f = cfg_dir / "app.yaml"
        f.write_text(
            "app_name: myapp\n"
            "server:\n"
            "  host: localhost\n"
            "  port: 8080\n"
            "database:\n"
            "  host: db.local\n"
            "  port: 5432\n"
            "  name: appdb\n"
        )

        data = RawConfigBuilder().from_file(f).build_dict()
        source = infer_schema(data, name="AppConfig")

        assert "class AppConfig(BaseModel):" in source
        assert "class ServerConfig(BaseModel):" in source
        assert "class DatabaseConfig(BaseModel):" in source
        assert "server: ServerConfig" in source
        assert "database: DatabaseConfig" in source

    def test_infer_from_json_config(self, cfg_dir):
        """Schema inference works with JSON-loaded configs."""
        f = cfg_dir / "app.json"
        f.write_text(
            '{\n'
            '  "name": "json-app",\n'
            '  "port": 3000,\n'
            '  "ratio": 0.75,\n'
            '  "active": true,\n'
            '  "tags": ["web", "api"]\n'
            '}\n'
        )

        data = RawConfigBuilder().from_file(f).build_dict()
        source = infer_schema(data, name="JsonConfig")

        assert "class JsonConfig(BaseModel):" in source
        assert "name: str" in source
        assert "port: int" in source
        assert "ratio: float" in source
        assert "active: bool" in source
        assert "tags: list[str]" in source

    def test_infer_writes_to_file(self, cfg_dir):
        """output_file parameter writes the generated source to disk."""
        data = {"name": "myapp", "port": 8080}
        out = cfg_dir / "generated_model.py"

        source = infer_schema(data, name="AppConfig", output_file=out)

        assert out.exists()
        written = out.read_text()
        assert written == source
        assert "class AppConfig(BaseModel):" in written

    def test_generated_source_is_valid_python(self, cfg_dir):
        """The generated source compiles without syntax errors."""
        f = cfg_dir / "app.yaml"
        f.write_text(
            "app_name: myapp\n"
            "server:\n"
            "  host: localhost\n"
            "  port: 8080\n"
        )

        data = RawConfigBuilder().from_file(f).build_dict()
        source = infer_schema(data, name="AppConfig")

        compile(source, "<generated>", "exec")

    def test_infer_from_multi_source_pipeline(self, cfg_dir):
        """Schema inference on data assembled from multiple sources."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\nport: 8000\n")

        override = cfg_dir / "override.json"
        override.write_text('{"debug": false, "api_key": "secret"}')

        data = (
            RawConfigBuilder()
            .from_file(base)
            .from_file(override)
            .build_dict()
        )
        source = infer_schema(data, name="AppConfig")

        assert "name: str" in source
        assert "port: int" in source
        assert "debug: bool" in source
        assert "api_key: str" in source

    def test_infer_from_directory_loaded_config(self, cfg_dir):
        """Schema inference from directory-loaded multi-file config."""
        conf = cfg_dir / "config"
        conf.mkdir()
        (conf / "server.yaml").write_text("host: 0.0.0.0\nport: 8080\n")
        (conf / "database.yaml").write_text("host: db.local\nname: appdb\n")

        data = RawConfigBuilder().from_directory(conf).build_dict()
        source = infer_schema(data, name="AppConfig")

        assert "class AppConfig(BaseModel):" in source
        assert "class ServerConfig(BaseModel):" in source
        assert "class DatabaseConfig(BaseModel):" in source

    def test_infer_empty_dict(self):
        """An empty config dict produces a model with 'pass'."""
        source = infer_schema({}, name="EmptyConfig")

        assert "class EmptyConfig(BaseModel):" in source
        assert "pass" in source
