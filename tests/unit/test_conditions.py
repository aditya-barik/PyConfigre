"""Test suite for pyconfigre.conditions — conditional loading helpers.

Covers env_is, env_in, when_all, when_any, _make_callable, _evaluate_condition,
and the when= parameter on all builder source methods.
"""

import os
from pathlib import Path

import pytest

from pyconfigre import RawConfigBuilder
from pyconfigre.conditions import (
    _make_callable,
    env_in,
    env_is,
    when_all,
    when_any,
)


class TestEnvIs:
    """Tests for env_is() condition helper."""

    def test_env_is_match(self) -> None:
        """Returns True when env var matches expected value."""
        os.environ["TEST_COND"] = "dev"
        try:
            assert env_is("TEST_COND", "dev")() is True
        finally:
            del os.environ["TEST_COND"]

    def test_env_is_mismatch(self) -> None:
        """Returns False when env var does not match."""
        os.environ["TEST_COND"] = "prod"
        try:
            assert env_is("TEST_COND", "dev")() is False
        finally:
            del os.environ["TEST_COND"]

    def test_env_is_unset(self) -> None:
        """Returns False when env var is not set."""
        os.environ.pop("TEST_COND_UNSET", None)
        assert env_is("TEST_COND_UNSET", "dev")() is False


class TestEnvIn:
    """Tests for env_in() condition helper."""

    def test_env_in_match(self) -> None:
        """Returns True when env var is in the allowed set."""
        os.environ["TEST_COND"] = "staging"
        try:
            assert env_in("TEST_COND", ["staging", "prod"])() is True
        finally:
            del os.environ["TEST_COND"]

    def test_env_in_mismatch(self) -> None:
        """Returns False when env var is not in the allowed set."""
        os.environ["TEST_COND"] = "dev"
        try:
            assert env_in("TEST_COND", ["staging", "prod"])() is False
        finally:
            del os.environ["TEST_COND"]


class TestWhenAllAny:
    """Tests for when_all() and when_any() composition."""

    def test_when_all_all_true(self) -> None:
        """when_all returns True when all conditions are True."""
        assert when_all(lambda: True, lambda: True)() is True

    def test_when_all_one_false(self) -> None:
        """when_all returns False when any condition is False."""
        assert when_all(lambda: True, lambda: False)() is False

    def test_when_any_one_true(self) -> None:
        """when_any returns True when any condition is True."""
        assert when_any(lambda: False, lambda: True)() is True

    def test_when_any_all_false(self) -> None:
        """when_any returns False when all conditions are False."""
        assert when_any(lambda: False, lambda: False)() is False


class TestMakeCallable:
    """Tests for _make_callable() normalisation."""

    def test_callable_passthrough(self) -> None:
        """Callable conditions are returned as-is."""
        fn = lambda: True  # noqa: E731
        assert _make_callable(fn) is fn

    def test_tuple_shorthand(self) -> None:
        """2-tuple is converted to env_is() call."""
        os.environ["TEST_COND"] = "val"
        try:
            assert _make_callable(("TEST_COND", "val"))() is True
        finally:
            del os.environ["TEST_COND"]

    def test_invalid_type_raises(self) -> None:
        """Non-callable, non-tuple raises TypeError."""
        with pytest.raises(TypeError, match="Condition must be"):
            _make_callable(42)


class TestWhenOnBuilderMethods:
    """Tests for when= parameter on RawConfigBuilder source methods."""

    def test_when_on_from_file_true(self, temp_dir: Path) -> None:
        """from_file loads when condition is True."""
        f = temp_dir / "config.yaml"
        f.write_text("key: loaded\n")

        result = (
            RawConfigBuilder()
            .from_file(f, when=lambda: True)
            .build_dict()
        )
        assert result["key"] == "loaded"

    def test_when_on_from_file_false(self, temp_dir: Path) -> None:
        """from_file skips when condition is False."""
        f = temp_dir / "config.yaml"
        f.write_text("key: loaded\n")

        result = (
            RawConfigBuilder()
            .from_file(f, when=lambda: False)
            .build_dict()
        )
        assert result == {}

    def test_when_on_from_dict_true(self) -> None:
        """from_dict merges when condition is True."""
        result = (
            RawConfigBuilder()
            .from_dict({"key": "val"}, when=lambda: True)
            .build_dict()
        )
        assert result["key"] == "val"

    def test_when_on_from_dict_false(self) -> None:
        """from_dict skips when condition is False."""
        result = (
            RawConfigBuilder()
            .from_dict({"key": "val"}, when=lambda: False)
            .build_dict()
        )
        assert result == {}

    def test_when_on_set_true(self) -> None:
        """set() applies when condition is True."""
        result = (
            RawConfigBuilder()
            .set("key", "val", when=lambda: True)
            .build_dict()
        )
        assert result["key"] == "val"

    def test_when_on_set_false(self) -> None:
        """set() skips when condition is False."""
        result = (
            RawConfigBuilder()
            .set("key", "val", when=lambda: False)
            .build_dict()
        )
        assert result == {}

    def test_when_on_from_env_true(self) -> None:
        """from_env loads when condition is True."""
        os.environ["WHEN_TEST_KEY"] = "env_val"
        try:
            result = (
                RawConfigBuilder()
                .from_env("WHEN_TEST_", when=lambda: True)
                .build_dict()
            )
        finally:
            del os.environ["WHEN_TEST_KEY"]
        assert result["key"] == "env_val"

    def test_when_on_from_env_false(self) -> None:
        """from_env skips when condition is False."""
        os.environ["WHEN_TEST_KEY"] = "env_val"
        try:
            result = (
                RawConfigBuilder()
                .from_env("WHEN_TEST_", when=lambda: False)
                .build_dict()
            )
        finally:
            del os.environ["WHEN_TEST_KEY"]
        assert result == {}

    def test_when_none_always_loads(self) -> None:
        """when=None (default) always loads the source."""
        result = (
            RawConfigBuilder()
            .from_dict({"key": "val"}, when=None)
            .build_dict()
        )
        assert result["key"] == "val"

    def test_when_tuple_shorthand(self) -> None:
        """2-tuple shorthand works as when= value."""
        os.environ["TEST_COND"] = "yes"
        try:
            result = (
                RawConfigBuilder()
                .from_dict({"key": "val"}, when=("TEST_COND", "yes"))
                .build_dict()
            )
        finally:
            del os.environ["TEST_COND"]
        assert result["key"] == "val"

    def test_when_on_from_env_layer_false(self, temp_dir: Path) -> None:
        """from_env_layer skips when condition is False."""
        (temp_dir / "base.yaml").write_text("key: base\n")
        result = (
            RawConfigBuilder()
            .from_env_layer(temp_dir, when=lambda: False)
            .build_dict()
        )
        assert result == {}

    def test_when_on_from_env_layer_true(self, temp_dir: Path) -> None:
        """from_env_layer loads when condition is True."""
        (temp_dir / "base.yaml").write_text("key: base\n")
        result = (
            RawConfigBuilder()
            .from_env_layer(temp_dir, when=lambda: True)
            .build_dict()
        )
        assert result["key"] == "base"
