"""Tests for fuzzy date validation utilities."""

import pytest

from stash_graphql_client.errors import StashIntegrationError
from stash_graphql_client.types.date_utils import (
    DatePrecision,
    FuzzyDate,
    normalize_date,
    parse_date_precision,
    validate_fuzzy_date,
)


class TestParseDatePrecision:
    """Tests for parse_date_precision function."""

    def test_parse_year_precision(self):
        """Test parsing year-only dates."""
        assert parse_date_precision("2024") == DatePrecision.YEAR
        assert parse_date_precision("1999") == DatePrecision.YEAR
        assert parse_date_precision("2000") == DatePrecision.YEAR

    def test_parse_month_precision(self):
        """Test parsing year-month dates."""
        assert parse_date_precision("2024-01") == DatePrecision.MONTH
        assert parse_date_precision("2024-06") == DatePrecision.MONTH
        assert parse_date_precision("2024-12") == DatePrecision.MONTH

    def test_parse_day_precision(self):
        """Test parsing full dates."""
        assert parse_date_precision("2024-01-01") == DatePrecision.DAY
        assert parse_date_precision("2024-06-15") == DatePrecision.DAY
        assert parse_date_precision("2024-12-31") == DatePrecision.DAY

    def test_parse_day_precision_with_time(self):
        """Test parsing full dates with time components."""
        assert parse_date_precision("2024-01-01 12:30:45") == DatePrecision.OTHER
        assert parse_date_precision("2024-06-15 00:00:00") == DatePrecision.OTHER

    def test_invalid_month(self):
        """Test that invalid months are rejected."""
        with pytest.raises(StashIntegrationError, match="Invalid month"):
            parse_date_precision("2024-00")
        with pytest.raises(StashIntegrationError, match="Invalid month"):
            parse_date_precision("2024-13")

    def test_invalid_day(self):
        """Test that invalid days are rejected."""
        with pytest.raises(StashIntegrationError, match="Invalid date"):
            parse_date_precision("2024-02-30")
        with pytest.raises(StashIntegrationError, match="Invalid date"):
            parse_date_precision("2024-04-31")

    def test_invalid_format(self):
        """Test that invalid formats are rejected."""
        with pytest.raises(StashIntegrationError, match="Invalid date format"):
            parse_date_precision("not-a-date")
        with pytest.raises(StashIntegrationError, match="Invalid date format"):
            parse_date_precision("2024-1")
        with pytest.raises(StashIntegrationError, match="Invalid date format"):
            parse_date_precision("2024-1-5")
        with pytest.raises(StashIntegrationError, match="Invalid date format"):
            parse_date_precision("")


class TestValidateFuzzyDate:
    """Tests for validate_fuzzy_date function."""

    def test_valid_dates(self):
        """Test that valid dates return True."""
        assert validate_fuzzy_date("2024") is True
        assert validate_fuzzy_date("2024-03") is True
        assert validate_fuzzy_date("2024-03-15") is True

    def test_invalid_dates(self):
        """Test that invalid dates return False."""
        assert validate_fuzzy_date("invalid") is False
        assert validate_fuzzy_date("2024-3") is False
        assert validate_fuzzy_date("2024-3-15") is False
        assert validate_fuzzy_date("") is False
        assert validate_fuzzy_date("2024-13") is False
        assert validate_fuzzy_date("2024-02-30") is False


class TestFuzzyDate:
    """Tests for FuzzyDate class."""

    def test_create_year_precision(self):
        """Test creating FuzzyDate with year precision."""
        date = FuzzyDate("2024")
        assert date.value == "2024"
        assert date.precision == DatePrecision.YEAR
        assert str(date) == "2024"

    def test_create_month_precision(self):
        """Test creating FuzzyDate with month precision."""
        date = FuzzyDate("2024-03")
        assert date.value == "2024-03"
        assert date.precision == DatePrecision.MONTH
        assert str(date) == "2024-03"

    def test_create_day_precision(self):
        """Test creating FuzzyDate with day precision."""
        date = FuzzyDate("2024-03-15")
        assert date.value == "2024-03-15"
        assert date.precision == DatePrecision.DAY
        assert str(date) == "2024-03-15"

    def test_create_invalid(self):
        """Test that invalid dates raise error."""
        with pytest.raises(StashIntegrationError):
            FuzzyDate("invalid")

    def test_equality(self):
        """Test equality comparison."""
        date1 = FuzzyDate("2024-03-15")
        date2 = FuzzyDate("2024-03-15")
        date3 = FuzzyDate("2024-03")
        date4 = FuzzyDate("2024")

        assert date1 == date2
        assert date1 != date3
        assert date1 != date4
        assert date3 != date4

    def test_repr(self):
        """Test string representation."""
        date = FuzzyDate("2024-03")
        assert repr(date) == "FuzzyDate(value='2024-03', precision=month)"

    def test_to_datetime_year(self):
        """Test converting year precision to datetime."""
        date = FuzzyDate("2024")
        dt = date.to_datetime()
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

    def test_to_datetime_month(self):
        """Test converting month precision to datetime."""
        date = FuzzyDate("2024-03")
        dt = date.to_datetime()
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 1

    def test_to_datetime_day(self):
        """Test converting day precision to datetime."""
        date = FuzzyDate("2024-03-15")
        dt = date.to_datetime()
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 15

    def test_to_datetime_day_with_time(self):
        """Test converting day precision with time to datetime (time stripped)."""
        date = FuzzyDate("2024-03-15 14:30:45")
        dt = date.to_datetime()
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 15
        # Time should be stripped, so it should be midnight
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0


class TestNormalizeDate:
    """Tests for normalize_date function."""

    def test_normalize_no_target(self):
        """Test normalization without target precision (validation only)."""
        assert normalize_date("2024") == "2024"
        assert normalize_date("2024-03") == "2024-03"
        assert normalize_date("2024-03-15") == "2024-03-15"

    def test_normalize_reduce_precision_to_year(self):
        """Test reducing precision to year."""
        assert normalize_date("2024-03-15", "year") == "2024"
        assert normalize_date("2024-03", "year") == "2024"
        assert normalize_date("2024", "year") == "2024"

    def test_normalize_reduce_precision_to_month(self):
        """Test reducing precision to month."""
        assert normalize_date("2024-03-15", "month") == "2024-03"
        assert normalize_date("2024-03", "month") == "2024-03"

    def test_normalize_expand_precision_from_year(self):
        """Test expanding precision from year."""
        assert normalize_date("2024", "month") == "2024-01"
        assert normalize_date("2024", "day") == "2024-01-01"

    def test_normalize_expand_precision_from_month(self):
        """Test expanding precision from month."""
        assert normalize_date("2024-03", "day") == "2024-03-01"
        assert normalize_date("2024-03", "month") == "2024-03"

    def test_normalize_day_stays_same(self):
        """Test that day precision stays same when target is day."""
        assert normalize_date("2024-03-15", "day") == "2024-03-15"

    def test_normalize_reduce_precision_other_to_day(self):
        """Test reducing precision from OTHER (datetime) to DAY."""
        assert normalize_date("2024-03-15 14:30:45", "day") == "2024-03-15"
        assert normalize_date("2024-12-31 23:59:59", "day") == "2024-12-31"

    def test_normalize_invalid_date(self):
        """Test that invalid dates raise error."""
        with pytest.raises(StashIntegrationError):
            normalize_date("invalid", "year")


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_leap_year_dates(self):
        """Test that leap year dates are handled correctly."""
        assert validate_fuzzy_date("2024-02-29") is True
        assert validate_fuzzy_date("2023-02-29") is False

    def test_boundary_dates(self):
        """Test boundary dates."""
        # First and last day of year
        assert validate_fuzzy_date("2024-01-01") is True
        assert validate_fuzzy_date("2024-12-31") is True

        # First and last month
        assert validate_fuzzy_date("2024-01") is True
        assert validate_fuzzy_date("2024-12") is True

    def test_old_dates(self):
        """Test very old dates."""
        assert validate_fuzzy_date("1900") is True
        assert validate_fuzzy_date("1900-01") is True
        assert validate_fuzzy_date("1900-01-01") is True

    def test_future_dates(self):
        """Test future dates."""
        assert validate_fuzzy_date("2100") is True
        assert validate_fuzzy_date("2100-12") is True
        assert validate_fuzzy_date("2100-12-31") is True

    def test_fuzzy_date_comparison_with_non_fuzzy(self):
        """Test that comparing FuzzyDate with non-FuzzyDate returns NotImplemented."""
        date = FuzzyDate("2024")
        assert date.__eq__("2024") == NotImplemented
        assert date.__eq__(2024) == NotImplemented

    def test_fuzzy_date_hash(self):
        """Test that FuzzyDate objects can be hashed for use in sets and dicts."""
        date1 = FuzzyDate("2024-03-15")
        date2 = FuzzyDate("2024-03-15")
        date3 = FuzzyDate("2024-03")
        date4 = FuzzyDate("2024")

        # Same dates should have same hash
        assert hash(date1) == hash(date2)

        # Different dates should (likely) have different hashes
        assert hash(date1) != hash(date3)
        assert hash(date1) != hash(date4)

        # Test usage in set - duplicates should be removed
        date_set = {date1, date2, date3, date4}
        assert len(date_set) == 3  # date1 and date2 are equal, so only 3 unique

        # Test usage as dict keys
        date_dict = {
            date1: "day precision",
            date3: "month precision",
            date4: "year precision",
        }
        assert date_dict[date2] == "day precision"  # date2 equals date1
        assert len(date_dict) == 3


class TestRealWorldUseCases:
    """Test real-world usage scenarios."""

    def test_performer_birthdate_year_only(self):
        """Test storing performer birthdate with year precision."""
        # Many performers only have birth year known
        birthdate = "1990"
        assert validate_fuzzy_date(birthdate) is True
        fuzzy = FuzzyDate(birthdate)
        assert fuzzy.precision == DatePrecision.YEAR

    def test_scene_date_month_precision(self):
        """Test storing scene date with month precision."""
        # Some scenes only have month/year
        date = "2024-03"
        assert validate_fuzzy_date(date) is True
        fuzzy = FuzzyDate(date)
        assert fuzzy.precision == DatePrecision.MONTH

    def test_normalizing_user_input(self):
        """Test normalizing various user inputs."""
        # User provides year, expand to full date for processing
        assert normalize_date("2024", "day") == "2024-01-01"

        # User provides full date, reduce for display
        assert normalize_date("2024-03-15", "year") == "2024"

    def test_batch_validation(self):
        """Test validating multiple dates at once."""
        dates = ["2024", "2024-03", "2024-03-15", "invalid"]
        valid = [d for d in dates if validate_fuzzy_date(d)]
        assert valid == ["2024", "2024-03", "2024-03-15"]

    def test_normalize_day_to_day_edge_case(self):
        """Test normalizing day precision to day (edge case for coverage)."""
        # This tests the else branch in normalize_date when reducing precision to DAY
        # which shouldn't normally be reached but ensures 100% coverage
        result = normalize_date("2024-03-15", "day")
        assert result == "2024-03-15"
