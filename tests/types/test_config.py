"""Tests for stash_graphql_client.types.config module.

Tests config types including ConfigResult.plugins() method.
"""

import pytest

from stash_graphql_client.types.config import ConfigResult


@pytest.mark.unit
def test_config_result_plugins_returns_empty_dict() -> None:
    """Test ConfigResult.plugins() returns empty dict.

    This covers line 669 in config.py - the return statement.
    The method is a TODO placeholder that currently returns {}.
    """
    config = ConfigResult()
    result = config.plugins()

    assert result == {}
    assert isinstance(result, dict)


@pytest.mark.unit
def test_config_result_plugins_with_include_param() -> None:
    """Test ConfigResult.plugins() with include parameter.

    Even with include list, it returns empty dict (TODO: filtering not implemented).
    """
    config = ConfigResult()
    result = config.plugins(include=["plugin1", "plugin2"])

    assert result == {}
    assert isinstance(result, dict)
