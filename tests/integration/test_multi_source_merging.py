"""
Use case: merging configuration from multiple sources.

This is the defining feature of PyConfigre. These tests verify that the
priority order (from_file → from_env → from_dict → set) is applied
correctly across all combinations, including deep nested merges, list
replacement, and mid-chain inspection with peek().
"""

import pytest

from pyconfigre import ConfigBuilder, DataClassConfigBuilder

from .conftest import AppConfig, SimpleConfig, SimpleConfigDC, env_vars


@pytest.mark.integration
class TestMultiSourceMerging:
    """Multiple sources are merged with correct priority."""

    def test_file_env_dict_priority_chain(self, cfg_dir):
        """file < env < dict: each layer overrides only what it touches.

        The canonical three-source pattern. Verifies that un-overridden
        keys survive intact through all layers.
        """
        f = cfg_dir / "base.yaml"
        f.write_text("name: from-file\ndebug: false\nport: 8000\n")

        with env_vars(SRC_NAME="from-env", SRC_DEBUG="true"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(f)  # name=from-file, debug=false, port=8000
                .from_env("SRC_")  # name=from-env, debug=true (port untouched)
                .from_dict({"port": 3000})  # port=3000 (name, debug untouched)
                .build()
            )

        assert config.name == "from-env"  # env won over file
        assert config.debug is True  # env won over file
        assert config.port == 3000  # dict won over env and file

    def test_two_files_second_wins_on_conflict(self, cfg_dir):
        """When two files share a key, the second file's value wins."""
        base = cfg_dir / "base.yaml"
        base.write_text("name: base-name\ndebug: false\nport: 8000\n")

        override = cfg_dir / "override.yaml"
        override.write_text("name: override-name\n")  # only overrides name

        config = ConfigBuilder(SimpleConfig).from_file(base).from_file(override).build()

        assert config.name == "override-name"  # second file wins
        assert config.debug is False  # preserved from base
        assert config.port == 8000  # preserved from base

    def test_dict_wins_over_file(self, cfg_dir):
        """from_dict() applied after from_file() overrides conflicting keys."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: from-file\nport: 8000\n")

        config = (
            ConfigBuilder(SimpleConfig)
            .from_file(f)
            .from_dict({"name": "from-dict", "api_key": "injected"})
            .build()
        )

        assert config.name == "from-dict"  # dict wins
        assert config.api_key == "injected"  # dict added new key
        assert config.port == 8000  # file value preserved

    def test_deep_nested_partial_override(self, cfg_dir):
        """A later source that partially overrides a nested dict preserves
        the sibling keys it does not mention.

        This is the deep-merge behaviour: source updates only the keys it
        provides; it does not wholesale replace the parent dict.
        """
        base = cfg_dir / "base.yaml"
        base.write_text(
            "app_name: base-app\n"
            "database:\n"
            "  host: localhost\n"
            "  port: 5432\n"
            "  name: base_db\n"
            "  username: base_user\n"
            "  password: base_pass\n"
        )

        override = cfg_dir / "override.yaml"
        override.write_text(
            "database:\n  host: prod-db.example.com\n"  # only host changes
        )

        config = ConfigBuilder(AppConfig).from_file(base).from_file(override).build()

        assert config.database.host == "prod-db.example.com"  # overridden
        assert config.database.port == 5432  # preserved
        assert config.database.name == "base_db"  # preserved
        assert config.database.username == "base_user"  # preserved

    def test_list_in_later_source_replaces_entirely(self, cfg_dir):
        """Lists are replaced wholesale, never extended.

        A list in config represents a complete value (e.g. allowed_hosts,
        middleware). A later source that provides the same key should replace
        the entire list, not append to it.
        """
        from pydantic import BaseModel

        class ListConfig(BaseModel):
            name: str = "x"
            hosts: list[str] = []

        base = cfg_dir / "base.yaml"
        base.write_text("hosts:\n  - host-a\n  - host-b\n  - host-c\n")

        override = cfg_dir / "override.yaml"
        override.write_text("hosts:\n  - host-new\n")

        config = ConfigBuilder(ListConfig).from_file(base).from_file(override).build()

        assert config.hosts == [
            "host-new"
        ]  # replaced, not ["host-a", "host-b", "host-c", "host-new"]

    def test_set_is_highest_priority(self, cfg_dir):
        """set() applied last wins over every other source."""
        f = cfg_dir / "app.yaml"
        f.write_text("name: from-file\nport: 8000\n")

        with env_vars(S_PORT="9000"):
            config = (
                ConfigBuilder(SimpleConfig)
                .from_file(f)
                .from_env("S_")
                .set("port", 1234)  # must beat both file and env
                .build()
            )

        assert config.port == 1234

    def test_peek_shows_intermediate_state(self, cfg_dir):
        """peek() returns a snapshot of what has been assembled so far.

        Calling peek() after from_file but before from_dict must not include
        the dict's values, and must not affect the final build().
        """
        f = cfg_dir / "app.yaml"
        f.write_text("name: file-value\nport: 8000\n")

        builder = ConfigBuilder(SimpleConfig).from_file(f)

        # Snapshot after file only
        mid = builder.peek()
        assert mid["name"] == "file-value"
        assert "api_key" not in mid

        # Continue building — peek() must not have consumed or altered state
        config = builder.from_dict({"api_key": "added-after-peek"}).build()
        assert config.name == "file-value"
        assert config.api_key == "added-after-peek"

    def test_dataclass_multi_source_priority(self, cfg_dir):
        """file < env < dict priority holds for DataClassConfigBuilder."""
        f = cfg_dir / "base.yaml"
        f.write_text("name: from-file\ndebug: false\nport: 8000\n")

        with env_vars(DC_NAME="from-env", DC_DEBUG="true"):
            config = (
                DataClassConfigBuilder(SimpleConfigDC, unknown_fields="ignore")
                .from_file(f)  # name=from-file, debug=false, port=8000
                .from_env("DC_")  # name=from-env, debug=true
                .from_dict({"port": 3000})  # port=3000
                .build()
            )

        assert config.name == "from-env"
        assert config.debug is True
        assert config.port == 3000
