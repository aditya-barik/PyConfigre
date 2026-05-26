"""Test suite for environment variable loader."""

import os

from pyconfigre.loaders import ENVLoader


class TestENVLoader:
    """Tests for ENVLoader class."""

    def test_load_env_with_prefix(self) -> None:
        """Test loading environment variables with prefix.

        Sets test environment variables with TESTAPP_ prefix and verifies
        they are loaded correctly with type parsing.  Single underscores in
        key names are preserved as-is (only double underscores trigger nesting).
        """
        os.environ["TESTAPP_DEBUG"] = "true"
        os.environ["TESTAPP_PORT"] = "9000"
        os.environ["TESTAPP_DATABASE_HOST"] = "localhost"

        try:
            loader = ENVLoader()
            config = loader(prefix="TESTAPP_")

            assert config["debug"] is True
            assert config["port"] == 9000
            # Single underscore stays as part of the flat key name
            assert config["database_host"] == "localhost"
        finally:
            del os.environ["TESTAPP_DEBUG"]
            del os.environ["TESTAPP_PORT"]
            del os.environ["TESTAPP_DATABASE_HOST"]

    def test_load_env_without_prefix(self) -> None:
        """Test loading all environment variables.

        Verifies that environment variables can be loaded without
        requiring a specific prefix.
        """
        os.environ["PYCONFIGRE_TEST_VAR"] = "test_value"

        try:
            loader = ENVLoader()
            config = loader()

            assert "pyconfigre_test_var" in config
            assert config["pyconfigre_test_var"] == "test_value"
        finally:
            del os.environ["PYCONFIGRE_TEST_VAR"]

    def test_env_no_strip_prefix(self) -> None:
        """Test keeping prefix in keys.

        Verifies that when strip_prefix=False, the prefix is retained
        in the configuration keys.
        """
        os.environ["APP_DEBUG"] = "true"

        try:
            loader = ENVLoader()
            config = loader(prefix="APP_", strip_prefix=False)

            assert "app_debug" in config
            assert config["app_debug"] is True
        finally:
            del os.environ["APP_DEBUG"]

    def test_env_no_lowercase(self) -> None:
        """Test keeping original case in keys.

        Verifies that when lowercase=False, the original case of
        environment variable names is preserved.
        """
        os.environ["DEBUG"] = "true"

        try:
            loader = ENVLoader()
            config = loader(lowercase=False)

            assert "DEBUG" in config
        finally:
            del os.environ["DEBUG"]

    def test_env_value_parsing(self) -> None:
        """Test intelligent value type parsing.

        Verifies that environment variable values are parsed into
        appropriate Python types (bool, int, float, None, str).
        """
        os.environ["TEST_BOOL_TRUE"] = "true"
        os.environ["TEST_BOOL_FALSE"] = "false"
        os.environ["TEST_INT"] = "42"
        os.environ["TEST_FLOAT"] = "3.14"
        os.environ["TEST_NONE"] = "null"
        os.environ["TEST_STRING"] = "hello"

        try:
            loader = ENVLoader()
            config = loader(prefix="TEST_")

            assert config["bool_true"] is True
            assert config["bool_false"] is False
            assert config["int"] == 42
            assert config["float"] == 3.14
            assert config["none"] is None
            assert config["string"] == "hello"
        finally:
            for key in [
                "TEST_BOOL_TRUE",
                "TEST_BOOL_FALSE",
                "TEST_INT",
                "TEST_FLOAT",
                "TEST_NONE",
                "TEST_STRING",
            ]:
                del os.environ[key]

    # ------------------------------------------------------------------
    # Double-underscore nesting (new in v0.1.1)
    # ------------------------------------------------------------------

    def test_double_underscore_nesting(self) -> None:
        """Test that double underscores expand into nested dicts.

        The universal convention for nested config via environment variables
        is ``__`` as a separator::

            MYAPP__DATABASE__HOST=localhost  →  {"database": {"host": "localhost"}}
        """
        os.environ["MYAPP__DATABASE__HOST"] = "localhost"
        os.environ["MYAPP__DATABASE__PORT"] = "5432"
        os.environ["MYAPP__APP__DEBUG"] = "true"

        try:
            loader = ENVLoader()
            config = loader(prefix="MYAPP__")

            assert config["database"]["host"] == "localhost"
            assert config["database"]["port"] == 5432
            assert config["app"]["debug"] is True
        finally:
            del os.environ["MYAPP__DATABASE__HOST"]
            del os.environ["MYAPP__DATABASE__PORT"]
            del os.environ["MYAPP__APP__DEBUG"]

    def test_single_underscore_not_nested(self) -> None:
        """Test that single underscores are not treated as separators.

        ``LOG_LEVEL`` must become ``log_level``, not ``{"log": {"level": ...}}``.
        Only double underscores trigger nesting.
        """
        os.environ["APP_LOG_LEVEL"] = "info"
        os.environ["APP_MAX_RETRIES"] = "3"

        try:
            loader = ENVLoader()
            config = loader(prefix="APP_")

            # Keys with single underscores stay flat
            assert config["log_level"] == "info"
            assert config["max_retries"] == 3
            # They must NOT be nested dicts
            assert not isinstance(config.get("log"), dict)
            assert not isinstance(config.get("max"), dict)
        finally:
            del os.environ["APP_LOG_LEVEL"]
            del os.environ["APP_MAX_RETRIES"]

    def test_nested_false_keeps_flat(self) -> None:
        """Test that nested=False disables double-underscore expansion.

        When a caller explicitly opts out of nesting, double underscores
        must be preserved verbatim in the flat key name.
        """
        os.environ["FLAT__DB__HOST"] = "localhost"

        try:
            loader = ENVLoader()
            config = loader(prefix="FLAT__", nested=False)

            # nested=False: key stays flat with __ intact
            assert config["db__host"] == "localhost"
            assert "db" not in config
        finally:
            del os.environ["FLAT__DB__HOST"]

    def test_nested_default_is_true(self) -> None:
        """Test that nested=True is the default behaviour.

        Calling the loader without the nested parameter must produce
        the same result as calling it with nested=True explicitly.
        """
        os.environ["DFLT__X__Y"] = "42"

        try:
            loader = ENVLoader()
            default_result = loader(prefix="DFLT__")
            explicit_result = loader(prefix="DFLT__", nested=True)

            assert default_result == explicit_result
            assert default_result["x"]["y"] == 42
        finally:
            del os.environ["DFLT__X__Y"]

    def test_mixed_single_and_double_underscore(self) -> None:
        """Test that single and double underscores coexist correctly.

        A prefix like ``APP_`` with a key ``APP_LOG_LEVEL`` (single) and
        ``APP__DB__HOST`` (double) in the same environment should produce:
        - ``log_level``: flat key (single underscore preserved)
        - ``db.host``: nested (double underscore expanded)

        This requires using no prefix so both are visible.
        """
        os.environ["MIX_LOG_LEVEL"] = "debug"
        os.environ["MIX__DB__HOST"] = "pg"

        try:
            loader = ENVLoader()
            config_single = loader(prefix="MIX_")  # strip MIX_ → log_level
            config_double = loader(
                prefix="MIX__"
            )  # strip MIX__ → db__host → {db:{host}}

            assert config_single["log_level"] == "debug"
            assert config_double["db"]["host"] == "pg"
        finally:
            del os.environ["MIX_LOG_LEVEL"]
            del os.environ["MIX__DB__HOST"]
