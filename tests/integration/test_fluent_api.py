"""
Use case: fluent API ergonomics.

These tests treat ConfigBuilder as a user would — chaining methods, using
set() with dot notation, inspecting state mid-chain with peek(), and
exercising the get_raw_data() deprecation path. They verify that the API
is composable, non-destructive, and gives clear errors when misused.
"""

import pytest

from pyconfigre import ConfigBuilder

from .conftest import AppConfig, SimpleConfig, env_vars


@pytest.mark.integration
class TestFluentAPI:
    """ConfigBuilder's fluent API composes correctly and fails gracefully."""

    def test_all_source_methods_chain(self, cfg_dir):
        """from_file → from_env → from_dict → set → build: full chain works."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: from-file\nport: 8000\n")

        with env_vars(CHAIN_DEBUG="true"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(f)
                .from_env("CHAIN_")
                .from_dict({"api_key": "from-dict"})
                .set("port", 5555)
                .build()
            )

        assert config.name == "from-file"
        assert config.debug is True
        assert config.api_key == "from-dict"
        assert config.port == 5555

    def test_peek_does_not_affect_build(self, cfg_dir):
        """Calling peek() mid-chain does not consume or alter builder state.

        peek() must be non-destructive: the builder continues normally
        after peek() is called, and build() produces the correct final result.
        """
        f = cfg_dir / "app.yaml"
        f.write_text("name: peek-test\nport: 8000\n")

        builder = ConfigBuilder(SimpleConfig).from_file(f)

        # Inspect mid-chain
        snapshot = builder.peek()
        assert snapshot["name"] == "peek-test"
        assert "api_key" not in snapshot

        # Continue — snapshot must not have consumed or forked state
        config = builder.from_dict({"api_key": "added-later"}).build()
        assert config.name == "peek-test"
        assert config.api_key == "added-later"

    def test_peek_returns_independent_copy(self, cfg_dir):
        """Mutating the dict returned by peek() does not affect the builder."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: copy-test\nport: 9090\n")

        builder = ConfigBuilder(SimpleConfig).from_file(f)
        snapshot = builder.peek()

        # Mutate the snapshot
        snapshot["name"] = "mutated"
        snapshot["port"] = 1111

        # Builder internal state must be unaffected
        config = builder.build()
        assert config.name == "copy-test"
        assert config.port == 9090

    def test_set_creates_nested_path_with_dot_notation(self):
        """set() with dot notation creates intermediate dicts as needed."""
        builder = ConfigBuilder(AppConfig)
        builder.set("database.host", "set-host")
        builder.set("database.port", 5432)
        builder.set("database.name", "setdb")
        builder.set("database.username", "setuser")
        builder.set("database.password", "setpass")
        builder.set("app_name", "set-app")

        config = builder.build()

        assert config.database.host == "set-host"
        assert config.database.port == 5432
        assert config.app_name == "set-app"

    def test_set_raises_clear_error_on_scalar_intermediate(self):
        """set() with a path that traverses a scalar gives a precise TypeError.

        The error message must name:
        - the full key path requested
        - the specific segment that is not a dict
        - the actual type of that segment
        """
        builder = ConfigBuilder(SimpleConfig)
        builder._data = {"name": "collision"}

        # "name" is a string — "name.sub" cannot traverse it
        with pytest.raises(TypeError) as exc_info:
            builder.set("name.sub", "value")

        message = str(exc_info.value)
        assert "name.sub" in message  # full path
        assert "name" in message  # offending segment
        assert "str" in message  # actual type

    def test_get_raw_data_emits_deprecation_warning(self, cfg_dir):
        """get_raw_data() is a deprecated alias for peek() and must warn."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: deprecated-test\n")

        builder = ConfigBuilder(SimpleConfig).from_file(f)

        with pytest.warns(DeprecationWarning, match="get_raw_data\\(\\) is deprecated"):
            raw = builder.get_raw_data()

        assert raw["name"] == "deprecated-test"

    def test_builder_is_reusable_after_peek(self, cfg_dir):
        """A builder can have sources added after peek() is called.

        peek() is non-terminal. The builder continues accumulating sources
        and produces the correct final result at build().
        """
        f = cfg_dir / "base.yaml"
        f.write_text("name: base\nport: 8000\n")

        builder = ConfigBuilder(SimpleConfig).from_file(f)

        # Snapshot after first source
        mid = builder.peek()
        assert mid["port"] == 8000

        # Add more sources
        builder.from_dict({"port": 9999, "api_key": "added"})

        # Final build must include all sources
        config = builder.build()
        assert config.port == 9999
        assert config.api_key == "added"
        assert config.name == "base"
