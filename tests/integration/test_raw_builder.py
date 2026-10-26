"""
Use case: schema-less configuration with RawConfigBuilder.

RawConfigBuilder is the foundation — no Pydantic, no dataclasses, just
dict-in / dict-out.  These tests verify realistic schema-less workflows:
multi-source merging, deep merge behaviour, peek/build isolation, and
field validation (unknown_fields / missing_fields) without a schema.
"""

import warnings

import pytest

from pyconfigre import RawConfigBuilder
from pyconfigre.exceptions import ConfigValidationError

from .conftest import env_vars


@pytest.mark.integration
class TestRawBuilderMultiSource:
    """RawConfigBuilder multi-source merging without any schema."""

    def test_file_env_dict_set_priority(self, cfg_dir):
        """file < env < dict < set: full priority chain as plain dict."""
        f = cfg_dir / "base.yaml"
        f.write_text("host: from-file\nport: 8000\ndebug: false\n")

        with env_vars(APP_HOST="from-env", APP_DEBUG="true"):
            result = (
                RawConfigBuilder()
                .from_file(f)
                .from_env("APP_")
                .from_dict({"port": 3000})
                .set("debug", False)
                .build_dict()
            )

        assert result["host"] == "from-env"
        assert result["port"] == 3000
        assert result["debug"] is False

    def test_deep_merge_preserves_siblings(self, cfg_dir):
        """Later sources partially override nested dicts without clobbering siblings."""
        base = cfg_dir / "base.yaml"
        base.write_text(
            "database:\n"
            "  host: localhost\n"
            "  port: 5432\n"
            "  name: mydb\n"
        )

        override = cfg_dir / "override.yaml"
        override.write_text("database:\n  host: prod-db.example.com\n")

        result = (
            RawConfigBuilder()
            .from_file(base)
            .from_file(override)
            .build_dict()
        )

        assert result["database"]["host"] == "prod-db.example.com"
        assert result["database"]["port"] == 5432
        assert result["database"]["name"] == "mydb"

    def test_list_replaced_not_appended(self, cfg_dir):
        """Lists are replaced wholesale, not merged or appended."""
        base = cfg_dir / "base.yaml"
        base.write_text("hosts:\n  - host-a\n  - host-b\n")

        override = cfg_dir / "override.yaml"
        override.write_text("hosts:\n  - host-new\n")

        result = (
            RawConfigBuilder()
            .from_file(base)
            .from_file(override)
            .build_dict()
        )

        assert result["hosts"] == ["host-new"]

    def test_two_files_different_formats(self, cfg_dir):
        """YAML base + JSON override merge correctly."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: myapp\nport: 8000\n")

        override = cfg_dir / "override.json"
        override.write_text('{"port": 9000, "api_key": "from-json"}')

        result = (
            RawConfigBuilder()
            .from_file(base)
            .from_file(override)
            .build_dict()
        )

        assert result["name"] == "myapp"
        assert result["port"] == 9000
        assert result["api_key"] == "from-json"

    def test_peek_returns_independent_snapshot(self, cfg_dir):
        """peek() returns a deep copy — mutations do not affect the builder."""
        f = cfg_dir / "base.yaml"
        f.write_text("name: myapp\nport: 8000\n")

        builder = RawConfigBuilder().from_file(f)

        snapshot = builder.peek()
        snapshot["name"] = "mutated"
        snapshot["port"] = 0

        result = builder.build_dict()
        assert result["name"] == "myapp"
        assert result["port"] == 8000

    def test_peek_then_continue_building(self, cfg_dir):
        """peek() is non-terminal — sources can be added after peek()."""
        f = cfg_dir / "base.yaml"
        f.write_text("name: myapp\nport: 8000\n")

        builder = RawConfigBuilder().from_file(f)

        mid = builder.peek()
        assert mid["port"] == 8000
        assert "api_key" not in mid

        result = builder.from_dict({"api_key": "added-later"}).build_dict()
        assert result["api_key"] == "added-later"
        assert result["name"] == "myapp"

    def test_empty_builder_returns_empty_dict(self):
        """A builder with no sources returns an empty dict."""
        result = RawConfigBuilder().build_dict()
        assert result == {}

    def test_build_dict_returns_independent_copy(self):
        """build_dict() returns a deep copy — mutations do not affect the builder."""
        builder = RawConfigBuilder().from_dict({"key": "value"})

        first = builder.build_dict()
        first["key"] = "mutated"

        second = builder.build_dict()
        assert second["key"] == "value"

    def test_set_dot_notation_creates_nested_path(self):
        """set() with dot-separated keys creates nested dicts."""
        result = (
            RawConfigBuilder()
            .set("database.host", "localhost")
            .set("database.port", 5432)
            .set("server.host", "0.0.0.0")
            .build_dict()
        )

        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
        assert result["server"]["host"] == "0.0.0.0"


@pytest.mark.integration
class TestRawBuilderFieldValidation:
    """RawConfigBuilder unknown_fields and missing_fields validation."""

    def test_unknown_fields_warn_by_default(self):
        """Extra keys emit a UserWarning by default."""
        with pytest.warns(UserWarning, match="Unknown fields"):
            RawConfigBuilder(
                expected_keys={"name", "port"},
            ).from_dict(
                {"name": "myapp", "port": 8000, "extra": "unexpected"}
            ).build_dict()

    def test_unknown_fields_forbid(self):
        """unknown_fields='forbid' raises ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Unknown fields"):
            RawConfigBuilder(
                expected_keys={"name", "port"},
                unknown_fields="forbid",
            ).from_dict(
                {"name": "myapp", "port": 8000, "extra": "unexpected"}
            ).build_dict()

    def test_unknown_fields_ignore(self):
        """unknown_fields='ignore' silently allows extra keys."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = (
                RawConfigBuilder(
                    expected_keys={"name", "port"},
                    unknown_fields="ignore",
                )
                .from_dict({"name": "myapp", "port": 8000, "extra": "yes"})
                .build_dict()
            )

        assert result["extra"] == "yes"

    def test_missing_fields_forbid_by_default(self):
        """Missing required keys raise ConfigValidationError by default."""
        with pytest.raises(ConfigValidationError, match="Missing required fields"):
            RawConfigBuilder(
                required_keys={"name", "port", "host"},
            ).from_dict(
                {"name": "myapp"}
            ).build_dict()

    def test_missing_fields_warn(self):
        """missing_fields='warn' emits a warning instead of raising."""
        with pytest.warns(UserWarning, match="Missing required fields"):
            result = (
                RawConfigBuilder(
                    required_keys={"name", "port"},
                    missing_fields="warn",
                )
                .from_dict({"name": "myapp"})
                .build_dict()
            )

        assert result["name"] == "myapp"

    def test_missing_fields_ignore(self):
        """missing_fields='ignore' silently allows missing keys."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = (
                RawConfigBuilder(
                    required_keys={"name", "port"},
                    missing_fields="ignore",
                )
                .from_dict({"name": "myapp"})
                .build_dict()
            )

        assert result["name"] == "myapp"

    def test_combined_unknown_and_missing_validation(self):
        """Both unknown and missing field checks fire in one build."""
        with pytest.raises(ConfigValidationError, match="Missing required fields"):
            RawConfigBuilder(
                required_keys={"name", "host"},
                expected_keys={"name", "host"},
                unknown_fields="forbid",
            ).from_dict(
                {"name": "myapp", "extra": "bad"}
            ).build_dict()
