"""
Use case: environment-layered configuration loading with ``from_env_layer()``.

The base → environment → local layering pattern is the most common
configuration strategy for web applications.  These tests verify the full
end-to-end flow across all three builders, with real files and environment
variables.
"""

import os

import pytest

from pyconfigre import ConfigBuilder, DataClassConfigBuilder, RawConfigBuilder

from .conftest import SimpleConfig, SimpleConfigDC, env_vars


@pytest.mark.integration
class TestEnvLayerLoading:
    """Environment-layered configuration in realistic pipelines."""

    def test_full_layer_stack(self, cfg_dir):
        """base → env-specific → local: all three layers merge correctly."""
        (cfg_dir / "base.yaml").write_text(
            "name: myapp\ndebug: false\nport: 8000\n"
        )
        (cfg_dir / "production.yaml").write_text("debug: false\nport: 443\n")
        (cfg_dir / "local.yaml").write_text("debug: true\n")

        with env_vars(APP_ENV="production"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_env_layer(cfg_dir, env_var="APP_ENV")
                .build()
            )

        assert config.name == "myapp"
        assert config.port == 443
        assert config.debug is True

    def test_dev_environment_default(self, cfg_dir):
        """Without env var set, defaults to 'development' layer."""
        (cfg_dir / "base.yaml").write_text("name: myapp\nport: 8000\n")
        (cfg_dir / "development.yaml").write_text("debug: true\nport: 3000\n")

        os.environ.pop("UNSET_ENV_VAR_XYZ", None)
        config = (
            ConfigBuilder(SimpleConfig)
            .from_env_layer(cfg_dir, env_var="UNSET_ENV_VAR_XYZ")
            .build()
        )

        assert config.port == 3000
        assert config.debug is True

    def test_missing_layers_silently_skipped(self, cfg_dir):
        """Missing layer files are silently skipped — only base exists."""
        (cfg_dir / "base.yaml").write_text("name: myapp\nport: 8000\n")

        config = (
            ConfigBuilder(SimpleConfig)
            .from_env_layer(cfg_dir)
            .build()
        )

        assert config.name == "myapp"
        assert config.port == 8000

    def test_env_layer_then_env_vars_override(self, cfg_dir):
        """Pattern: file layers provide defaults, env vars override secrets.

        The canonical production pattern — config files in the repo provide
        structure and defaults, environment variables inject secrets and
        deployment-specific values.
        """
        (cfg_dir / "base.yaml").write_text(
            "name: myapp\ndebug: false\nport: 8000\n"
        )
        (cfg_dir / "production.yaml").write_text("port: 443\n")

        with env_vars(
            DEPLOY_ENV="production",
            SVC_API_KEY="prod-secret-key",
        ):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_env_layer(cfg_dir, env_var="DEPLOY_ENV")
                .from_env("SVC_")
                .build()
            )

        assert config.port == 443
        assert config.api_key == "prod-secret-key"

    def test_env_layer_with_json_extension(self, cfg_dir):
        """Environment layers work with JSON files via custom extension."""
        (cfg_dir / "base.json").write_text(
            '{"name": "json-app", "port": 8000}'
        )
        (cfg_dir / "staging.json").write_text('{"port": 9000}')

        with env_vars(APP_ENV="staging"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_env_layer(cfg_dir, env_var="APP_ENV", extension=".json")
                .build()
            )

        assert config.name == "json-app"
        assert config.port == 9000

    def test_env_layer_custom_names(self, cfg_dir):
        """Custom base_name and local_name override the defaults."""
        (cfg_dir / "defaults.yaml").write_text("name: myapp\nport: 8000\n")
        (cfg_dir / "overrides.yaml").write_text("port: 9999\n")

        config = (
            ConfigBuilder(SimpleConfig)
            .from_env_layer(
                cfg_dir, base_name="defaults", local_name="overrides"
            )
            .build()
        )

        assert config.name == "myapp"
        assert config.port == 9999

    def test_env_layer_with_dataclass_builder(self, cfg_dir):
        """from_env_layer works through DataClassConfigBuilder."""
        (cfg_dir / "base.yaml").write_text(
            "name: dc-app\ndebug: false\nport: 8000\n"
        )
        (cfg_dir / "staging.yaml").write_text("port: 9000\n")

        with env_vars(DC_ENV="staging"):
            config = (
                DataClassConfigBuilder(SimpleConfigDC)
                .from_env_layer(cfg_dir, env_var="DC_ENV")
                .build()
            )

        assert config.name == "dc-app"
        assert config.port == 9000

    def test_env_layer_with_raw_builder(self, cfg_dir):
        """from_env_layer works through RawConfigBuilder (schema-less)."""
        (cfg_dir / "base.yaml").write_text("host: localhost\nport: 8000\n")
        (cfg_dir / "production.yaml").write_text("host: prod.example.com\n")

        with env_vars(RAW_ENV="production"):
            result = (
                RawConfigBuilder()
                .from_env_layer(cfg_dir, env_var="RAW_ENV")
                .build_dict()
            )

        assert result["host"] == "prod.example.com"
        assert result["port"] == 8000

    def test_env_layer_combined_with_directory(self, cfg_dir):
        """Pattern: env layers for app config + directory for component configs."""
        app_dir = cfg_dir / "app"
        app_dir.mkdir()
        (app_dir / "base.yaml").write_text("app_name: myapp\n")
        (app_dir / "production.yaml").write_text("app_name: myapp-prod\n")

        components = cfg_dir / "components"
        components.mkdir()
        (components / "server.yaml").write_text("host: 0.0.0.0\nport: 8080\n")
        (components / "database.yaml").write_text("host: db.local\nname: mydb\n")

        with env_vars(APP_ENV="production"):
            result = (
                RawConfigBuilder()
                .from_env_layer(app_dir, env_var="APP_ENV")
                .from_directory(components)
                .build_dict()
            )

        assert result["app_name"] == "myapp-prod"
        assert result["server"]["host"] == "0.0.0.0"
        assert result["database"]["name"] == "mydb"
