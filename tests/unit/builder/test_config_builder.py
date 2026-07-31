"""Test suite for pyconfigre.builder.config_builder — ConfigBuilder.

This module contains unit tests for ConfigBuilder, including Pydantic
validation, multi-source priority, integration workflows, and inheritance
from RawConfigBuilder.
"""

import os
from pathlib import Path

import pytest
from tests.conftest import ComplexConfig, SimpleConfig

from pyconfigre import ConfigBuilder, RawConfigBuilder
from pyconfigre.exceptions import ConfigValidationError

# —— ConfigBuilder (Child-class) Tests ————————————————————————————————————————————


class TestConfigBuilder:
    """Smoke tests for ConfigBuilder — inherited pipeline → build()."""

    def test_build_basic_config(self) -> None:
        """Test building simple configuration.

        Verifies that ConfigBuilder can create a validated configuration
        object with default values from the Pydantic model.
        """
        config: SimpleConfig = ConfigBuilder(SimpleConfig).build()

        assert config.app_name == "test_app"
        assert config.debug is False
        assert config.port == 8000

    def test_from_file_yaml(self, yaml_config_file: Path) -> None:
        """Test loading configuration from YAML file.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config: ComplexConfig = (
            ConfigBuilder(ComplexConfig).from_file(yaml_config_file).build()
        )

        assert config.app_name == "test_application_yaml"
        assert config.debug is True
        assert config.port == 9000

    def test_from_file_json(self, json_config_file: Path) -> None:
        """Test loading configuration from JSON file.

        Parameters
        ----------
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        config: ComplexConfig = (
            ConfigBuilder(ComplexConfig).from_file(json_config_file).build()
        )

        assert config.app_name == "test_application_json"
        assert config.debug is True

    def test_from_file_optional_missing(self, temp_dir: Path) -> None:
        """Test optional file parameter with missing file.

        Verifies that missing optional files do not raise an error
        and configuration continues with defaults.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        nonexistent = temp_dir / "missing.yaml"

        config: SimpleConfig = (
            ConfigBuilder(SimpleConfig).from_file(nonexistent, optional=True).build()
        )

        assert config.app_name == "test_app"

    def test_from_env(self) -> None:
        """Test loading from environment variables.

        Sets environment variables and verifies they are loaded and
        properly type-parsed by the builder.
        """
        os.environ["SIMPLE_APP_NAME"] = "env_app"
        os.environ["SIMPLE_DEBUG"] = "true"
        os.environ["SIMPLE_PORT"] = "3000"

        try:
            config: SimpleConfig = (
                ConfigBuilder(SimpleConfig).from_env(prefix="SIMPLE_").build()
            )

            assert config.app_name == "env_app"
            assert config.debug is True
            assert config.port == 3000
        finally:
            for key in ["SIMPLE_APP_NAME", "SIMPLE_DEBUG", "SIMPLE_PORT"]:
                del os.environ[key]

    def test_from_dict(self) -> None:
        """Test loading from dictionary.

        Verifies that ConfigBuilder can load configuration from
        a Python dictionary.
        """
        config: SimpleConfig = (
            ConfigBuilder(SimpleConfig)
            .from_dict({"app_name": "dict_app", "port": 5000})
            .build()
        )

        assert config.app_name == "dict_app"
        assert config.port == 5000

    def test_set_value(self) -> None:
        """Test setting individual configuration values.

        Verifies that ConfigBuilder.set() can override individual
        configuration values.
        """
        config: SimpleConfig = (
            ConfigBuilder(SimpleConfig)
            .set("app_name", "set_app")
            .set("port", 7000)
            .build()
        )

        assert config.app_name == "set_app"
        assert config.port == 7000

    def test_set_nested_value(self) -> None:
        """Test setting nested configuration values.

        Verifies that ConfigBuilder.set() supports dot notation
        for setting nested configuration values.
        """
        config: ComplexConfig = (
            ConfigBuilder(ComplexConfig)
            .set("app_name", "test_app")
            .set("debug", True)
            .set("server.host", "example.com")
            .set("server.port", 5432)
            .build()
        )

        assert config.server["host"] == "example.com"
        assert config.server["port"] == 5432

    def test_multiple_sources_priority(
        self, yaml_config_file: Path, json_config_file: Path
    ) -> None:
        """Test priority merging of multiple sources.

        Verifies that when loading from multiple sources, later sources
        override earlier ones (YAML → JSON → dict).

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        config: ComplexConfig = (
            ConfigBuilder(ComplexConfig)
            .from_file(yaml_config_file)
            .from_file(json_config_file)
            .from_dict({"port": 7000})
            .build()
        )

        assert config.app_name == "test_application_json"
        assert config.port == 7000


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_complete_workflow(
        self, yaml_config_file: Path, json_config_file: Path
    ) -> None:
        """Test complete configuration loading workflow.

        Tests loading config from YAML, JSON, environment variables,
        and direct set() calls with proper priority ordering.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        os.environ["MYAPP_PORT"] = "6000"

        try:
            config: ComplexConfig = (
                ConfigBuilder(ComplexConfig)
                .from_file(yaml_config_file)
                .from_file(json_config_file)
                .from_env("MYAPP_")
                .set("debug", False)
                .build()
            )

            assert config.app_name == "test_application_json"
            assert config.port == 6000
            assert config.debug is False
        finally:
            del os.environ["MYAPP_PORT"]

    def test_yaml_yml_extension_detection(self, temp_dir: Path) -> None:
        """Test both .yaml and .yml extensions are detected.

        Verifies that ConfigLoader correctly handles both .yaml and .yml
        file extensions.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        from pyconfigre.loaders import ConfigLoader

        yaml_file = temp_dir / "config.yaml"
        yml_file = temp_dir / "config.yml"

        content = "app_name: test\ndebug: false\nport: 8000"
        yaml_file.write_text(content)
        yml_file.write_text(content)

        yaml_config = ConfigLoader.detect_and_load(yaml_file)
        yml_config = ConfigLoader.detect_and_load(yml_file)

        assert yaml_config == yml_config


class TestConfigBuilderValidation:
    """Test for Pydantic validation — ConfigBuilder-specific behavior."""

    def test_validation_error_on_invalid_type(self) -> None:
        """Test validation error when config has invalid types."""
        builder = ConfigBuilder(SimpleConfig)

        with pytest.raises(
            ConfigValidationError, match="Configuration validation failed"
        ):
            builder.from_dict({"port": "not_a_number"}).build()


# —— Inheritance Tests ————————————————————————————————————————————


class TestBuilderInheritance:
    """Test verifying ConfigBuilder inheritance from RawConfigBuilder."""

    def test_config_builder_is_instance_of_raw_config_builder(self) -> None:
        """Test that ConfigBuilder is a subclass of RawConfigBuilder.

        Verifies the inheritance relationship established in v0.2.0
        where ConfigBuilder extends RawConfigBuilder.
        """
        config_builder = ConfigBuilder(SimpleConfig)

        assert isinstance(config_builder, RawConfigBuilder)

    def test_config_builder_inherits_all_pipeline_methods(
        self, yaml_config_file: Path
    ) -> None:
        """Test that ConfigBuilder inherits all pipeline methods from RawConfigBuilder.

        All pipeline methods must be callable on ConfigBuilder and
        return self for fluent chaining.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config_builder = ConfigBuilder(SimpleConfig)

        assert config_builder.from_file(yaml_config_file) is config_builder
        assert config_builder.from_dict({"port": 7000}) is config_builder
        assert config_builder.set("debug", False) is config_builder

        peeked = config_builder.peek()
        assert isinstance(peeked, dict)
        assert peeked["app_name"] == "test_application_yaml"
        assert peeked["port"] == 7000
        assert peeked["debug"] is False

    def test_build_dict_available_on_config_builder(self) -> None:
        """Test that build_dict() is callable on ConfigBuilder.

        ConfigBuilder inherits build_dict() from rawConfigBuilder,
        allowing users to get a plain dictionary even when a schema
        is available.
        """
        config_builder = (
            ConfigBuilder(SimpleConfig)
            .from_dict({"app_name": "inherited", "port": 5000})
            .build_dict()
        )

        assert isinstance(config_builder, dict)
        assert config_builder["app_name"] == "inherited"
        assert config_builder["port"] == 5000
