"""Tests for stash_graphql_client.types.config module."""

import pytest

from stash_graphql_client.types.config import ConfigResult


class TestConfigResult:
    """Tests for ConfigResult class."""

    @pytest.fixture
    def config_result(self) -> ConfigResult:
        """Create a ConfigResult instance for testing using model_construct.

        model_construct is Pydantic's built-in method for creating instances
        without validation. This is appropriate here because we're only testing
        the plugins() method which doesn't depend on any of the nested fields.
        """
        return ConfigResult.model_construct(
            general=None,
            interface=None,
            dlna=None,
            defaults=None,
            ui={},
        )

    @pytest.mark.unit
    def test_plugins_returns_empty_dict(self, config_result: ConfigResult) -> None:
        """Test that plugins() returns an empty dict.

        This exercises the stub implementation that currently returns {}.
        """
        result = config_result.plugins()
        assert result == {}
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_plugins_with_include_parameter(self, config_result: ConfigResult) -> None:
        """Test that plugins() accepts include parameter and still returns empty dict."""
        result = config_result.plugins(include=["plugin1", "plugin2"])
        assert result == {}
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_plugins_with_none_include(self, config_result: ConfigResult) -> None:
        """Test that plugins() works with explicit None include parameter."""
        result = config_result.plugins(include=None)
        assert result == {}
