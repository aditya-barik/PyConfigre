"""
Use case: handling unsupported file formats.

Verifies the error ordering fix from Issue-1 (extension checked before
existence), the behaviour of optional=True with bad extensions, and the
custom loader registration path that makes new formats supported.
"""

import pytest

from pyconfigre import ConfigBuilder
from pyconfigre.loaders import BaseLoader, ConfigLoader

from .conftest import SimpleConfig


@pytest.mark.integration
class TestUnsupportedFormats:
    """Unsupported file extensions are rejected with clear, immediate errors."""

    def test_ini_file_exists_raises_value_error(self, cfg_dir):
        """.ini file that exists on disk raises ValueError, not ConfigLoadError.

        The error is about the *format* not being recognised, which is a
        programmer mistake. It surfaces before any I/O on the file content.
        """
        f = cfg_dir / "config.ini"
        f.write_text("[section]\nkey = value\n")

        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigBuilder(SimpleConfig).from_file(f).build()

    def test_cfg_file_exists_raises_value_error(self, cfg_dir):
        """.cfg file that exists on disk raises ValueError immediately."""
        f = cfg_dir / "settings.cfg"
        f.write_text("key=value\n")

        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigBuilder(SimpleConfig).from_file(f).build()

    def test_unsupported_extension_missing_file_raises_value_error(self, cfg_dir):
        """An unsupported extension on a non-existent file raises ValueError.

        This is the Issue-1 fix: extension is validated before existence. The
        user gets a clear format error immediately, not a misleading
        ConfigNotFoundError that suggests the problem is the path, not the type.
        """
        missing = cfg_dir / "config.xyz"
        # File intentionally does NOT exist

        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigBuilder(SimpleConfig).from_file(missing).build()

    def test_optional_true_does_not_suppress_bad_extension(self, cfg_dir):
        """optional=True silences missing-file errors only — not format errors.

        A bad extension is always a programmer mistake and must always raise,
        regardless of whether the caller marked the file as optional.
        """
        missing_bad_ext = cfg_dir / "config.xyz"

        with pytest.raises(ValueError, match="Unsupported file format"):
            ConfigBuilder(SimpleConfig).from_file(
                missing_bad_ext, optional=True
            ).build()

    def test_custom_loader_makes_extension_supported(self, cfg_dir):
        """Registering a custom loader makes a previously-unsupported extension work.

        This verifies the full extensibility path: register a loader for .ini,
        then from_file() on an .ini file succeeds end-to-end.
        """

        class IniLoader(BaseLoader):
            """Minimal INI loader that parses key=value pairs in [DEFAULT]."""

            def __call__(self, path, **kwargs):
                import configparser

                parser = configparser.ConfigParser()
                parser.read(path)
                # Flatten DEFAULT section into a plain dict
                return dict(parser.defaults())

        f = cfg_dir / "config.ini"
        f.write_text("[DEFAULT]\nname = ini-service\nport = 6060\n")

        try:
            ConfigLoader.register_loader("ini", IniLoader(), extensions=[".ini"])

            config = ConfigBuilder(SimpleConfig).from_file(f).build()

            assert config.name == "ini-service"
            # configparser returns strings; Pydantic coerces "6060" → 6060
            assert config.port == 6060

        finally:
            ConfigLoader.reset()
