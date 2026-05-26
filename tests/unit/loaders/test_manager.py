"""Test suite for ConfigLoader manager."""

from pathlib import Path

import pytest

from pyconfigre.loaders import BaseLoader, ConfigLoader


class TestConfigLoader:
    """Tests for ConfigLoader manager class."""

    def test_detect_and_load_yaml(self, yaml_config_file: Path) -> None:
        """Test auto-detection and loading of YAML file.

        Parameters
        ----------
        yaml_config_file : Path
            Fixture providing a temporary YAML config file.
        """
        config = ConfigLoader.detect_and_load(yaml_config_file)

        assert config["app_name"] == "test_application_yaml"
        assert config["debug"] is True

    def test_detect_and_load_json(self, json_config_file: Path) -> None:
        """Test auto-detection and loading of JSON file.

        Parameters
        ----------
        json_config_file : Path
            Fixture providing a temporary JSON config file.
        """
        config = ConfigLoader.detect_and_load(json_config_file)

        assert config["app_name"] == "test_application_json"
        assert config["debug"] is True

    def test_detect_and_load_toml(self, toml_config_file: Path) -> None:
        """Test auto-detection and loading of TOML file.

        Parameters
        ----------
        toml_config_file : Path
            Fixture providing a temporary TOML config file.
        """
        config = ConfigLoader.detect_and_load(toml_config_file)

        assert config["app_name"] == "test_application_toml"
        assert config["debug"] is True

    def test_detect_unsupported_extension(self, temp_dir: Path) -> None:
        """Test error for unsupported file extension.

        The extension is validated before file existence is checked, so
        this raises ValueError even when the file exists on disk.

        Parameters
        ----------
        temp_dir : Path
            Fixture providing a temporary directory.
        """
        unsupported_file = temp_dir / "config.ini"
        unsupported_file.write_text("")

        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigLoader.detect_and_load(unsupported_file)

    def test_get_registered_loaders(self) -> None:
        """Test retrieving list of registered loaders."""
        loaders = ConfigLoader.list_loaders()

        assert "yaml" in loaders
        assert "json" in loaders
        assert "toml" in loaders
        assert "env" in loaders

    def test_list_extensions(self) -> None:
        """Test retrieving registered file extensions."""
        extensions = ConfigLoader.list_extensions()

        assert ".yaml" in extensions
        assert ".yml" in extensions
        assert ".json" in extensions
        assert ".toml" in extensions

    # ------------------------------------------------------------------
    # validate_extension (new in v0.1.1)
    # ------------------------------------------------------------------

    def test_validate_extension_known_with_dot(self) -> None:
        """Test that validate_extension returns the loader type for a known
        extension supplied with a leading dot.
        """
        assert ConfigLoader.validate_extension(".yaml") == "yaml"
        assert ConfigLoader.validate_extension(".yml") == "yaml"
        assert ConfigLoader.validate_extension(".json") == "json"
        assert ConfigLoader.validate_extension(".toml") == "toml"

    def test_validate_extension_known_without_dot(self) -> None:
        """Test that validate_extension normalises extensions that lack a
        leading dot, so ``"yaml"`` is treated identically to ``".yaml"``.
        """
        assert ConfigLoader.validate_extension("yaml") == "yaml"
        assert ConfigLoader.validate_extension("json") == "json"
        assert ConfigLoader.validate_extension("toml") == "toml"

    def test_validate_extension_case_insensitive(self) -> None:
        """Test that validate_extension normalises to lower-case so that
        ``.YAML``, ``.Yaml``, and ``.yaml`` all resolve correctly.
        """
        assert ConfigLoader.validate_extension(".YAML") == "yaml"
        assert ConfigLoader.validate_extension(".JSON") == "json"
        assert ConfigLoader.validate_extension(".TOML") == "toml"

    def test_validate_extension_unknown_raises(self) -> None:
        """Test that validate_extension raises ValueError for an unregistered
        extension with a message that names the bad extension.
        """
        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigLoader.validate_extension(".xyz")

    def test_validate_extension_unknown_message_includes_supported(self) -> None:
        """Test that the ValueError message lists the supported extensions
        so the developer knows what values are valid.
        """
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.validate_extension(".ini")

        message = str(exc_info.value)
        assert ".yaml" in message or "yaml" in message


class TestConfigLoaderErrorHandling:
    """Test error handling in ConfigLoader."""

    def test_get_unregistered_loader(self) -> None:
        """Test error when requesting unregistered loader type."""
        with pytest.raises(ValueError, match="Unknown loader type"):
            ConfigLoader.get_loader("nonexistent")

    def test_register_invalid_loader_type(self) -> None:
        """Test error when registering non-BaseLoader object."""
        with pytest.raises(TypeError, match="must be a BaseLoader instance"):
            ConfigLoader.register_loader("invalid", "not a loader")

    def test_register_loader_with_extensions(self) -> None:
        """Test registering custom loader with extensions.

        Uses ConfigLoader.reset() in teardown to avoid polluting other tests.
        """

        class DummyLoader(BaseLoader):
            def __call__(self, *args, **kwargs) -> dict:  # pragma: no cover
                return {"test": "value"}

        try:
            ConfigLoader.register_loader(
                "dummy", DummyLoader(), extensions=[".dummy", "dmy"]
            )

            assert "dummy" in ConfigLoader._loader_registry
            assert ".dummy" in ConfigLoader._extension_registry
            assert ".dmy" in ConfigLoader._extension_registry
            assert ConfigLoader._extension_registry[".dummy"] == "dummy"
        finally:
            ConfigLoader.reset()

    def test_get_loader_returns_singleton(self) -> None:
        """Test that get_loader returns the same instance each time."""
        loader1 = ConfigLoader.get_loader("yaml")
        loader2 = ConfigLoader.get_loader("yaml")

        assert loader1 is loader2

    def test_list_loaders_contains_all_defaults(self) -> None:
        """Test that list_loaders shows all expected default loaders."""
        loaders = ConfigLoader.list_loaders()

        assert len(loaders) >= 4
        assert all(loader in loaders for loader in ["yaml", "json", "toml", "env"])

    def test_list_extensions_mapping(self) -> None:
        """Test that extensions are properly mapped to loaders."""
        extensions = ConfigLoader.list_extensions()

        assert extensions.get(".yaml") == "yaml"
        assert extensions.get(".yml") == "yaml"
        assert extensions.get(".json") == "json"
        assert extensions.get(".toml") == "toml"

    # ------------------------------------------------------------------
    # reset() (new in v0.1.1)
    # ------------------------------------------------------------------

    def test_reset_removes_custom_loader(self) -> None:
        """Test that reset() removes a loader registered after import.

        After reset(), the custom loader type must not appear in
        :meth:`~pyconfigre.loaders.ConfigLoader.list_loaders`.
        """

        class TempLoader(BaseLoader):
            def __call__(self, *args, **kwargs) -> dict:  # pragma: no cover
                return {}

        ConfigLoader.register_loader("temp", TempLoader())
        assert "temp" in ConfigLoader.list_loaders()

        ConfigLoader.reset()

        assert "temp" not in ConfigLoader.list_loaders()

    def test_reset_removes_custom_extension(self) -> None:
        """Test that reset() removes extensions registered after import.

        After reset(), the custom extension must not appear in
        :meth:`~pyconfigre.loaders.ConfigLoader.list_extensions`.
        """

        class TempLoader(BaseLoader):
            def __call__(self, *args, **kwargs) -> dict:  # pragma: no cover
                return {}

        ConfigLoader.register_loader("temp2", TempLoader(), extensions=[".tmp"])
        assert ".tmp" in ConfigLoader.list_extensions()

        ConfigLoader.reset()

        assert ".tmp" not in ConfigLoader.list_extensions()

    def test_reset_preserves_builtin_loaders(self) -> None:
        """Test that reset() restores exactly the built-in loaders.

        All four built-in loaders (yaml, json, toml, env) must be
        present after reset().
        """

        class TempLoader(BaseLoader):
            def __call__(self, *args, **kwargs) -> dict:  # pragma: no cover
                return {}

        ConfigLoader.register_loader("will_be_gone", TempLoader())
        ConfigLoader.reset()

        loaders = ConfigLoader.list_loaders()
        assert "yaml" in loaders
        assert "json" in loaders
        assert "toml" in loaders
        assert "env" in loaders
        assert "will_be_gone" not in loaders

    def test_reset_is_idempotent(self) -> None:
        """Test that calling reset() multiple times is safe and does not
        corrupt the built-in snapshot.
        """
        ConfigLoader.reset()
        ConfigLoader.reset()

        assert "yaml" in ConfigLoader.list_loaders()

    def test_reset_raises_if_snapshot_not_taken(self) -> None:
        """Test that reset() raises RuntimeError when the built-in snapshot
        has not been taken yet.

        This guards the edge case where someone imports ``ConfigLoader``
        directly from ``pyconfigre.loaders.manager`` without going through
        the ``pyconfigre`` package, which is the only path that calls
        ``_save_builtin_snapshot()``.

        The test temporarily nulls the snapshot and must restore it in
        ``finally`` to avoid breaking the rest of the suite.
        """
        original = ConfigLoader._builtin_snapshot
        try:
            ConfigLoader._builtin_snapshot = None
            with pytest.raises(RuntimeError, match="Import 'pyconfigre' at least once"):
                ConfigLoader.reset()
        finally:
            ConfigLoader._builtin_snapshot = original

    def test_save_builtin_snapshot_is_idempotent(self) -> None:
        """Test that calling ``_save_builtin_snapshot()`` a second time is a
        no-op and does not overwrite the first snapshot.

        This protects against double-import scenarios where the module
        initialisation code runs more than once.
        """
        first_snapshot = ConfigLoader._builtin_snapshot
        ConfigLoader._save_builtin_snapshot()  # second call — must be no-op
        assert ConfigLoader._builtin_snapshot is first_snapshot
