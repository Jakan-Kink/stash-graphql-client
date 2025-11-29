"""Stash GraphQL Client logging utilities.

This module provides specialized loggers for Stash operations:
- client_logger - For Stash client operations
- processing_logger - For Stash data processing

Loggers use Python's standard logging module by default but can be
reconfigured by the consuming application.
"""

import logging
import sys
from pprint import pformat
from typing import Any


# Create base logger for stash operations
stash_logger = logging.getLogger("stash_graphql_client")

# Create specialized loggers
client_logger = logging.getLogger("stash_graphql_client.client")
processing_logger = logging.getLogger("stash_graphql_client.processing")


def configure_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    handler: logging.Handler | None = None,
) -> None:
    """Configure stash_graphql_client logging.

    Args:
        level: Logging level (default: INFO)
        format_string: Optional format string for log messages
        handler: Optional handler to use (default: StreamHandler to stderr)

    Example:
        >>> from stash_graphql_client.logging import configure_logging
        >>> configure_logging(level=logging.DEBUG)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if handler is None:
        handler = logging.StreamHandler(sys.stderr)

    handler.setFormatter(logging.Formatter(format_string))
    stash_logger.addHandler(handler)
    stash_logger.setLevel(level)


def debug_print(obj: Any, logger_name: str | None = None) -> None:
    """Debug printing with proper formatting.

    Args:
        obj: Object to format and log
        logger_name: Optional logger name to use (e.g., "processing", "client")
                    If None, uses root stash logger
    """
    try:
        formatted = pformat(obj, indent=2).strip()
        if logger_name == "client":
            client_logger.debug(formatted)
        elif logger_name == "processing":
            processing_logger.debug(formatted)
        elif logger_name:
            logging.getLogger(f"stash_graphql_client.{logger_name}").debug(formatted)
        else:
            stash_logger.debug(formatted)
    except Exception as e:
        print(f"Failed to log debug message: {e}", file=sys.stderr)


__all__ = [
    "client_logger",
    "configure_logging",
    "debug_print",
    "processing_logger",
    "stash_logger",
]
