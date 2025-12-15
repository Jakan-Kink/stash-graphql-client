"""Tests for stash_graphql_client.logging module.

Tests logging utilities including configure_logging() and debug_print().
"""

import logging
import sys
from io import StringIO

import pytest

from stash_graphql_client.logging import (
    client_logger,
    configure_logging,
    debug_print,
    processing_logger,
    stash_logger,
)


@pytest.mark.unit
def test_configure_logging_with_defaults() -> None:
    """Test configure_logging() with default parameters.

    This covers lines 41-49 in logging.py - default format_string and handler creation.
    """
    # Clear any existing handlers
    stash_logger.handlers.clear()

    # Call with defaults
    configure_logging()

    # Verify handler was added
    assert len(stash_logger.handlers) == 1
    handler = stash_logger.handlers[0]

    # Verify it's a StreamHandler to stderr
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream == sys.stderr

    # Verify formatter was set with default format
    assert handler.formatter is not None
    assert "%(asctime)s" in handler.formatter._fmt
    assert "%(name)s" in handler.formatter._fmt
    assert "%(levelname)s" in handler.formatter._fmt
    assert "%(message)s" in handler.formatter._fmt

    # Verify level was set
    assert stash_logger.level == logging.INFO


@pytest.mark.unit
def test_configure_logging_with_custom_level() -> None:
    """Test configure_logging() with custom level."""
    stash_logger.handlers.clear()

    configure_logging(level=logging.DEBUG)

    assert stash_logger.level == logging.DEBUG


@pytest.mark.unit
def test_configure_logging_with_custom_format() -> None:
    """Test configure_logging() with custom format string."""
    stash_logger.handlers.clear()

    custom_format = "%(levelname)s - %(message)s"
    configure_logging(format_string=custom_format)

    handler = stash_logger.handlers[0]
    assert handler.formatter._fmt == custom_format


@pytest.mark.unit
def test_configure_logging_with_custom_handler() -> None:
    """Test configure_logging() with custom handler."""
    stash_logger.handlers.clear()

    # Create custom handler
    custom_stream = StringIO()
    custom_handler = logging.StreamHandler(custom_stream)

    configure_logging(handler=custom_handler)

    # Verify custom handler was used
    assert len(stash_logger.handlers) == 1
    assert stash_logger.handlers[0] is custom_handler
    assert stash_logger.handlers[0].stream is custom_stream


@pytest.mark.unit
def test_debug_print_with_client_logger() -> None:
    """Test debug_print() with 'client' logger name.

    This covers lines 62-63 in logging.py.
    """
    # Set up handler to capture output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    client_logger.addHandler(handler)
    client_logger.setLevel(logging.DEBUG)

    try:
        test_obj = {"key": "value", "number": 42}
        debug_print(test_obj, logger_name="client")

        output = stream.getvalue()
        assert "key" in output
        assert "value" in output
        assert "42" in output
    finally:
        client_logger.removeHandler(handler)


@pytest.mark.unit
def test_debug_print_with_processing_logger() -> None:
    """Test debug_print() with 'processing' logger name.

    This covers lines 64-65 in logging.py.
    """
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    processing_logger.addHandler(handler)
    processing_logger.setLevel(logging.DEBUG)

    try:
        test_obj = {"processing": True, "data": [1, 2, 3]}
        debug_print(test_obj, logger_name="processing")

        output = stream.getvalue()
        assert "processing" in output
        assert "True" in output
    finally:
        processing_logger.removeHandler(handler)


@pytest.mark.unit
def test_debug_print_with_custom_logger_name() -> None:
    """Test debug_print() with custom logger name.

    This covers lines 66-67 in logging.py.
    """
    custom_logger = logging.getLogger("stash_graphql_client.custom")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    custom_logger.addHandler(handler)
    custom_logger.setLevel(logging.DEBUG)

    try:
        test_obj = {"custom": "logger"}
        debug_print(test_obj, logger_name="custom")

        output = stream.getvalue()
        assert "custom" in output
        assert "logger" in output
    finally:
        custom_logger.removeHandler(handler)


@pytest.mark.unit
def test_debug_print_with_no_logger_name() -> None:
    """Test debug_print() with no logger name (uses root stash logger).

    This covers lines 68-69 in logging.py.
    """
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    stash_logger.addHandler(handler)
    stash_logger.setLevel(logging.DEBUG)

    try:
        test_obj = {"root": "logger"}
        debug_print(test_obj)  # No logger_name specified

        output = stream.getvalue()
        assert "root" in output
        assert "logger" in output
    finally:
        stash_logger.removeHandler(handler)


@pytest.mark.unit
def test_debug_print_exception_handling(capfd) -> None:
    """Test debug_print() exception handling.

    This covers lines 70-71 in logging.py - exception handling when formatting fails.
    """

    # Create an object that will fail to format
    class UnformattableObject:
        def __repr__(self):
            raise RuntimeError("Cannot format this object")

    obj = UnformattableObject()

    # Should not raise, but print error to stderr
    debug_print(obj)

    # Capture stderr output
    captured = capfd.readouterr()
    assert "Failed to log debug message" in captured.err
