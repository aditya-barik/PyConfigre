"""Test suite for pyconfigre.builder._merge — _deep_merge helper.

This module contains unit tests for the deep-merge utility used by
RawConfigBuilder and inherited by ConfigBuilder.
"""

from pyconfigre.builder import _deep_merge

# —— Shared Utilities Tests ————————————————————————————————————————————


class TestDeepMerge:
    """Test deep merge functionality.

    ``_deep_merge`` is a module-level function in ``pyconfigre.builder``.
    Tests import it directly to verify its logic in isolation, independently
    of any builder class.
    """

    def test_deep_merge_nested_dicts(self) -> None:
        """Test merging nested dictionaries."""
        target = {"nested": {"a": 1, "b": 2}}
        source = {"nested": {"b": 3, "c": 4}}

        _deep_merge(target, source)

        assert target["nested"]["a"] == 1
        assert target["nested"]["b"] == 3
        assert target["nested"]["c"] == 4

    def test_deep_merge_overwrites_non_dict(self) -> None:
        """Test that deep merge overwrites non-dict values."""
        target = {"value": "original"}
        source = {"value": "updated"}

        _deep_merge(target, source)

        assert target["value"] == "updated"

    def test_deep_merge_with_lists(self) -> None:
        """Test that lists are replaced, not merged.

        Lists represent complete values in config files (e.g. allowed_hosts)
        and must be replaced wholesale by a later source.
        """
        target = {"items": [1, 2, 3]}
        source = {"items": [4, 5]}

        _deep_merge(target, source)

        assert target["items"] == [4, 5]

    def test_deep_merge_with_none_values(self) -> None:
        """Test merging with None values."""
        target = {"key": "value"}
        source = {"key": None}

        _deep_merge(target, source)

        assert target["key"] is None

    def test_deep_merge_preserves_unmatched_keys(self) -> None:
        """Test that unmatched keys are preserved."""
        target = {"a": 1, "b": 2}
        source = {"c": 3}

        _deep_merge(target, source)

        assert target["a"] == 1
        assert target["b"] == 2
        assert target["c"] == 3

    def test_deep_merge_module_level_import(self) -> None:
        """Test that _deep_merge is importable and callable at module level.

        Confirms the function is accessible from pyconfigre.builder for any
        future sibling classes (e.g. RawConfigBuilder) that need to reuse it.
        """
        target: dict = {}
        _deep_merge(target, {"x": {"y": 1}})
        assert target == {"x": {"y": 1}}
