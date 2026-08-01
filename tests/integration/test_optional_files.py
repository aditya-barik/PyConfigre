"""
Use case: optional file loading.

The optional=True parameter is one of the most important ergonomics features
of PyConfigre — it enables the base-file + environment-override pattern that
most real applications use. These tests verify every variant of that pattern.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.exceptions import ConfigNotFoundError

from .conftest import SimpleConfig, env_vars


@pytest.mark.integration
class TestOptionalFiles:
    """optional=True silences missing-file errors and allows fallback sources."""

    def test_optional_missing_file_is_silently_skipped(self, cfg_dir):
        """optional=True on a non-existent file: no error, chain continues."""
        missing = cfg_dir / "does_not_exist.yaml"

        config = (
            ConfigBuilder(SimpleConfig)
            .from_file(missing, optional=True)  # silently skipped
            .from_dict({"name": "fallback-value"})
            .build()
        )

        assert config.name == "fallback-value"

    def test_optional_existing_file_loads_normally(self, cfg_dir):
        """optional=True on an existing file loads it exactly as required=True would."""
        f = cfg_dir / "present.yaml"
        f.write_text("name: present-value\nport: 7777\n")

        config = ConfigBuilder(SimpleConfig).from_file(f, optional=True).build()

        assert config.name == "present-value"
        assert config.port == 7777

    def test_optional_missing_file_env_provides_all_values(self, cfg_dir):
        """Pattern: optional base file + required env vars.

        Common in CI/CD: no config file is deployed; all values come from
        environment variables. The optional file flag enables this gracefully.
        """
        missing = cfg_dir / "config.yaml"

        with env_vars(
            MYAPP_NAME="ci-service",
            MYAPP_DEBUG="false",
            MYAPP_PORT="8080",
        ):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(missing, optional=True)
                .from_env("MYAPP_")
                .build()
            )

        assert config.name == "ci-service"
        assert config.debug is False
        assert config.port == 8080

    def test_required_missing_file_raises(self, cfg_dir):
        """optional=False (default) on a non-existent file raises ConfigNotFoundError"""
        missing = cfg_dir / "required.yaml"

        with pytest.raises(ConfigNotFoundError, match="not found"):
            ConfigBuilder(SimpleConfig).from_file(missing).build()

    def test_base_required_environment_override_optional(self, cfg_dir):
        """Pattern: required base file + optional environment-specific override.

        The most common real-world pattern:
        - base.yaml: required — provides all defaults
        - prod.yaml / staging.yaml: optional — environment-specific overrides
        - local.yaml: optional — developer-local tweaks (gitignored)
        """
        base = cfg_dir / "base.yaml"
        base.write_text("name: base-app\ndebug: false\nport: 8000\n")

        # Environment-specific file — exists (simulating staging)
        staging = cfg_dir / "staging.yaml"
        staging.write_text("debug: true\nport: 9000\n")

        # Local override — does not exist (simulating a colleague without local.yaml)
        local = cfg_dir / "local.yaml"

        config = (
            ConfigBuilder(SimpleConfig)
            .from_file(base)  # required — must exist
            .from_file(staging, optional=True)  # exists → loaded
            .from_file(local, optional=True)  # missing → skipped
            .build()
        )

        assert config.name == "base-app"  # from base, untouched by staging
        assert config.debug is True  # overridden by staging
        assert config.port == 9000  # overridden by staging
