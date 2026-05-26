"""Shared test fixtures for PyConfigre test suite.

This module provides common pytest fixtures used across all test modules.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel


class SimpleConfig(BaseModel):
    """Simple test configuration model."""

    app_name: str = "test_app"
    debug: bool = False
    port: int = 8000


class ComplexConfig(BaseModel):
    """Complex nested configuration model."""

    app_name: str
    debug: bool
    port: int = 9000
    server: dict[str, Any]


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def yaml_config_file(temp_dir: Path) -> Path:
    """Create temporary YAML configuration file."""
    config_content = """
app_name: test_application_yaml
debug: true
port: 9000
server:
  host: localhost
  port: 5432
"""
    config_file = temp_dir / "config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def json_config_file(temp_dir: Path) -> Path:
    """Create temporary JSON configuration file."""
    config_content = """{
  "app_name": "test_application_json",
  "debug": true,
  "port": 9000,
  "server": {
    "host": "localhost",
    "port": 5432
  }
}"""
    config_file = temp_dir / "config.json"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def toml_config_file(temp_dir: Path) -> Path:
    """Create temporary TOML configuration file."""
    config_content = """
app_name = "test_application_toml"
debug = true
port = 9000

[server]
host = "localhost"
port = 5432
"""
    config_file = temp_dir / "config.toml"
    config_file.write_text(config_content)
    return config_file
