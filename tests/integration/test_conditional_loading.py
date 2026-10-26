"""
Use case: conditional source loading with the ``when=`` parameter.

Real applications load different configuration depending on the deployment
environment.  These tests verify the ``when=`` parameter on builder source
methods using the condition helpers (``env_is``, ``env_in``, ``when_all``,
``when_any``) in realistic multi-source pipelines.
"""

import pytest

from pyconfigre import (
    ConfigBuilder,
    RawConfigBuilder,
    env_in,
    env_is,
    when_all,
    when_any,
)

from .conftest import SimpleConfig, env_vars


@pytest.mark.integration
class TestConditionalLoading:
    """Conditional source loading in realistic pipelines."""

    def test_dev_only_file_loaded_in_dev(self, cfg_dir):
        """A dev-only config file is loaded when ENV=dev."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\ndebug: false\nport: 8000\n")

        dev = cfg_dir / "dev.yaml"
        dev.write_text("debug: true\nport: 3000\n")

        with env_vars(APP_ENV="dev"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(dev, when=env_is("APP_ENV", "dev"))
                .build()
            )

        assert config.debug is True
        assert config.port == 3000
        assert config.name == "myapp"

    def test_dev_only_file_skipped_in_prod(self, cfg_dir):
        """A dev-only config file is skipped when ENV=prod."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\ndebug: false\nport: 8000\n")

        dev = cfg_dir / "dev.yaml"
        dev.write_text("debug: true\nport: 3000\n")

        with env_vars(APP_ENV="prod"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(dev, when=env_is("APP_ENV", "dev"))
                .build()
            )

        assert config.debug is False
        assert config.port == 8000

    def test_env_in_loads_for_matching_environments(self, cfg_dir):
        """env_in condition loads source when env var is in the allowed set."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\nport: 8000\n")

        secure = cfg_dir / "secure.yaml"
        secure.write_text("api_key: prod-secret\n")

        with env_vars(DEPLOY_ENV="staging"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(secure, when=env_in("DEPLOY_ENV", ["staging", "prod"]))
                .build()
            )

        assert config.api_key == "prod-secret"

    def test_env_in_skips_for_excluded_environment(self, cfg_dir):
        """env_in condition skips source when env var is not in the set."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\nport: 8000\n")

        secure = cfg_dir / "secure.yaml"
        secure.write_text("api_key: prod-secret\n")

        with env_vars(DEPLOY_ENV="dev"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(secure, when=env_in("DEPLOY_ENV", ["staging", "prod"]))
                .build()
            )

        assert config.api_key is None

    def test_when_all_requires_both_conditions(self, cfg_dir):
        """when_all loads source only when all sub-conditions are met."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\ndebug: false\nport: 8000\n")

        perf = cfg_dir / "perf.yaml"
        perf.write_text("port: 9999\n")

        with env_vars(APP_ENV="prod", ENABLE_PERF="true"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(
                    perf,
                    when=when_all(
                        env_is("APP_ENV", "prod"),
                        env_is("ENABLE_PERF", "true"),
                    ),
                )
                .build()
            )

        assert config.port == 9999

    def test_when_all_skips_when_one_condition_fails(self, cfg_dir):
        """when_all skips source if any sub-condition is False."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\ndebug: false\nport: 8000\n")

        perf = cfg_dir / "perf.yaml"
        perf.write_text("port: 9999\n")

        with env_vars(APP_ENV="prod", ENABLE_PERF="false"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(
                    perf,
                    when=when_all(
                        env_is("APP_ENV", "prod"),
                        env_is("ENABLE_PERF", "true"),
                    ),
                )
                .build()
            )

        assert config.port == 8000

    def test_when_any_loads_if_one_matches(self, cfg_dir):
        """when_any loads source when at least one sub-condition is met."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\nport: 8000\n")

        ssl = cfg_dir / "ssl.yaml"
        ssl.write_text("port: 443\n")

        with env_vars(APP_ENV="staging"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(
                    ssl,
                    when=when_any(
                        env_is("APP_ENV", "staging"),
                        env_is("APP_ENV", "prod"),
                    ),
                )
                .build()
            )

        assert config.port == 443

    def test_conditional_env_loading(self):
        """from_env with when= loads env vars only when condition is met."""
        with env_vars(APP_ENV="prod", PROD_NAME="production-app", PROD_PORT="443"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_dict({"name": "default-app", "port": 8000})
                .from_env("PROD_", when=env_is("APP_ENV", "prod"))
                .build()
            )

        assert config.name == "production-app"
        assert config.port == 443

    def test_conditional_env_skipped(self):
        """from_env with when= skips env vars when condition is not met."""
        with env_vars(APP_ENV="dev", PROD_NAME="production-app", PROD_PORT="443"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_dict({"name": "default-app", "port": 8000})
                .from_env("PROD_", when=env_is("APP_ENV", "prod"))
                .build()
            )

        assert config.name == "default-app"
        assert config.port == 8000

    def test_conditional_dict_override(self):
        """from_dict with when= applies overrides conditionally."""
        with env_vars(FEATURE_FLAG="enabled"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_dict({"name": "myapp", "debug": False, "port": 8000})
                .from_dict(
                    {"debug": True},
                    when=env_is("FEATURE_FLAG", "enabled"),
                )
                .build()
            )

        assert config.debug is True

    def test_conditional_set(self):
        """set() with when= applies a single value conditionally."""
        with env_vars(OVERRIDE_PORT="yes"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_dict({"name": "myapp", "port": 8000})
                .set("port", 9999, when=env_is("OVERRIDE_PORT", "yes"))
                .build()
            )

        assert config.port == 9999

    def test_multi_conditional_pipeline(self, cfg_dir):
        """Multiple conditional sources in one pipeline — real-world pattern.

        Pattern: base file always loaded, then conditionally layer on
        environment-specific file, secrets from env vars, and a debug override.
        """
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\ndebug: false\nport: 8000\n")

        staging = cfg_dir / "staging.yaml"
        staging.write_text("port: 9000\n")

        with env_vars(
            APP_ENV="staging",
            SECRETS_API_KEY="staging-key",
        ):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(base)
                .from_file(staging, when=env_is("APP_ENV", "staging"))
                .from_env("SECRETS_", when=env_in("APP_ENV", ["staging", "prod"]))
                .set("debug", True, when=env_is("APP_ENV", "staging"))
                .build()
            )

        assert config.name == "myapp"
        assert config.port == 9000
        assert config.api_key == "staging-key"
        assert config.debug is True

    def test_raw_builder_conditional_loading(self, cfg_dir):
        """when= works on RawConfigBuilder (schema-less) pipelines."""
        f = cfg_dir / "base.yaml"
        f.write_text("host: localhost\nport: 8000\n")

        with env_vars(APP_ENV="prod"):
            result = (
                RawConfigBuilder()
                .from_file(f)
                .from_dict({"port": 443}, when=env_is("APP_ENV", "prod"))
                .build_dict()
            )

        assert result["host"] == "localhost"
        assert result["port"] == 443
