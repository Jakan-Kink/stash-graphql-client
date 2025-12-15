"""Date validation utilities for fuzzy date support (Stash v0.30.0+).

Stash PR #6359 added support for partial date formats:
- YYYY-MM-DD (day precision)
- YYYY-MM (month precision)
- YYYY (year precision)

This module provides utilities to validate and work with these fuzzy dates.
"""

# ruff: noqa: DTZ001
# Note: FuzzyDate represents calendar dates (birthdates, release dates), not timestamps.
# Calendar dates are timezone-agnostic and should use naive datetimes.

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal

from stash_graphql_client.errors import StashIntegrationError


class DatePrecision(str, Enum):
    """Date precision levels supported by Stash.
    These correspond to the database precision values:
    - DAY = 0 (YYYY-MM-DD)
    - MONTH = 1 (YYYY-MM)
    - YEAR = 2 (YYYY)
    - OTHER = 3 (YYYY-MM-DD HH:MM:SS - more precise than day)
    """

    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    OTHER = "other"


# Regex patterns for each date format
_DATE_PATTERNS = {
    DatePrecision.OTHER: re.compile(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    ),  # Date with time
    DatePrecision.DAY: re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # Date only
    DatePrecision.MONTH: re.compile(r"^\d{4}-\d{2}$"),
    DatePrecision.YEAR: re.compile(r"^\d{4}$"),
}


class FuzzyDate:
    """Represents a date with variable precision.

    Examples:
        >>> date = FuzzyDate("2024")
        >>> date.precision
        <DatePrecision.YEAR: 'year'>
        >>> date.value
        '2024'

        >>> date = FuzzyDate("2024-03")
        >>> date.precision
        <DatePrecision.MONTH: 'month'>

        >>> date = FuzzyDate("2024-03-15")
        >>> date.precision
        <DatePrecision.DAY: 'day'>
    """

    def __init__(self, value: str):
        """Initialize a fuzzy date from a string.

        Args:
            value: Date string in format YYYY, YYYY-MM, or YYYY-MM-DD

        Raises:
            StashIntegrationError: If the date format is invalid
        """
        self.value = value
        self.precision = parse_date_precision(value)

    def __str__(self) -> str:
        """Return the string representation of the date."""
        return self.value

    def __repr__(self) -> str:
        """Return a detailed representation."""
        return f"FuzzyDate(value={self.value!r}, precision={self.precision.value})"

    def __eq__(self, other: object) -> bool:
        """Compare fuzzy dates by value and precision."""
        if not isinstance(other, FuzzyDate):
            return NotImplemented
        return self.value == other.value and self.precision == other.precision

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return hash((self.value, self.precision))

    def to_datetime(self) -> datetime:
        """Convert to a datetime object (using first day of period).

        Returns:
            datetime: A datetime object representing the start of the period.
                - Year precision: January 1st of that year
                - Month precision: 1st day of that month
                - Day precision: That specific day (time stripped if present)

        Examples:
            >>> FuzzyDate("2024").to_datetime()
            datetime.datetime(2024, 1, 1, 0, 0)
            >>> FuzzyDate("2024-03").to_datetime()
            datetime.datetime(2024, 3, 1, 0, 0)
            >>> FuzzyDate("2024-03-15").to_datetime()
            datetime.datetime(2024, 3, 15, 0, 0)
        """
        if self.precision == DatePrecision.YEAR:
            return datetime(int(self.value), 1, 1)
        if self.precision == DatePrecision.MONTH:
            year, month = self.value.split("-")
            return datetime(int(year), int(month), 1)
        # DAY - strip time component if present
        date_part = self.value.split()[0] if " " in self.value else self.value
        return datetime.fromisoformat(date_part)


def parse_date_precision(date_str: str) -> DatePrecision:
    """Parse a date string and determine its precision level.

    Args:
        date_str: Date string to parse

    Returns:
        DatePrecision: The precision level of the date

    Raises:
        StashIntegrationError: If the date format is invalid

    Examples:
        >>> parse_date_precision("2024")
        <DatePrecision.YEAR: 'year'>
        >>> parse_date_precision("2024-03")
        <DatePrecision.MONTH: 'month'>
        >>> parse_date_precision("2024-03-15")
        <DatePrecision.DAY: 'day'>
    """
    # Try to match each pattern in order of specificity
    for precision, pattern in _DATE_PATTERNS.items():
        if pattern.match(date_str):
            # Validate the actual date values
            if precision in (DatePrecision.DAY, DatePrecision.OTHER):
                try:
                    # Strip time component if present for validation
                    date_part = date_str.split()[0] if " " in date_str else date_str
                    datetime.fromisoformat(date_part)
                except ValueError as e:
                    raise StashIntegrationError(f"Invalid date: {date_str}. {e}") from e
            elif precision == DatePrecision.MONTH:
                _, month = date_str.split("-")
                if not (1 <= int(month) <= 12):
                    raise StashIntegrationError(
                        f"Invalid month in date: {date_str}. Month must be 01-12."
                    )
            # Year validation is simple - just needs to be 4 digits

            return precision

    raise StashIntegrationError(
        f"Invalid date format: {date_str}. Expected YYYY, YYYY-MM, or YYYY-MM-DD."
    )


def validate_fuzzy_date(date_str: str) -> bool:
    """Validate that a date string is in a supported fuzzy format.

    Args:
        date_str: Date string to validate

    Returns:
        bool: True if the date is valid, False otherwise

    Examples:
        >>> validate_fuzzy_date("2024")
        True
        >>> validate_fuzzy_date("2024-03")
        True
        >>> validate_fuzzy_date("2024-03-15")
        True
        >>> validate_fuzzy_date("2024-3-15")
        False
        >>> validate_fuzzy_date("invalid")
        False
    """
    try:
        parse_date_precision(date_str)
        return True
    except StashIntegrationError:
        return False


def normalize_date(
    date_str: str, target_precision: Literal["day", "month", "year"] | None = None
) -> str:
    """Normalize a date string to a specific precision.

    Args:
        date_str: Date string to normalize
        target_precision: Target precision level. If None, returns the date as-is
            after validation.

    Returns:
        str: Normalized date string

    Raises:
        StashIntegrationError: If the date format is invalid or conversion fails

    Examples:
        >>> normalize_date("2024-03-15", "month")
        '2024-03'
        >>> normalize_date("2024-03-15", "year")
        '2024'
        >>> normalize_date("2024", "day")
        '2024-01-01'
    """
    fuzzy_date = FuzzyDate(date_str)

    if target_precision is None:
        return fuzzy_date.value

    target = DatePrecision(target_precision)
    # If already at target precision or lower, return as-is
    precision_order = [
        DatePrecision.YEAR,
        DatePrecision.MONTH,
        DatePrecision.DAY,
        DatePrecision.OTHER,
    ]
    if precision_order.index(fuzzy_date.precision) <= precision_order.index(target):
        # Need to expand precision
        dt = fuzzy_date.to_datetime()
        if target == DatePrecision.DAY:
            return dt.strftime("%Y-%m-%d")
        if target == DatePrecision.MONTH:
            return dt.strftime("%Y-%m")
        return dt.strftime("%Y")
    # Need to reduce precision
    if target == DatePrecision.YEAR:
        return fuzzy_date.value[:4]
    if target == DatePrecision.MONTH:
        return fuzzy_date.value[:7]
    # target == DatePrecision.DAY, strip time component
    return fuzzy_date.value.split()[0] if " " in fuzzy_date.value else fuzzy_date.value
