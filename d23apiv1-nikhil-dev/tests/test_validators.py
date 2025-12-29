"""
Tests for Input Validators

Tests birth date, time, and place validation.
"""

import pytest
from bot.validators.birth_details import (
    validate_birth_date,
    validate_birth_time,
    validate_birth_place,
    validate_all_birth_details,
    ValidationResult,
)


class TestBirthDateValidation:
    """Test birth date validation."""

    @pytest.mark.parametrize("date_input,expected_valid,expected_normalized", [
        # Standard formats
        ("15-08-1990", True, "15-08-1990"),
        ("15/08/1990", True, "15-08-1990"),
        ("1990-08-15", True, "15-08-1990"),

        # Various separators
        ("15.08.1990", True, "15-08-1990"),
        ("15 08 1990", True, "15-08-1990"),

        # Short year
        ("15-08-90", True, "15-08-1990"),

        # Edge cases
        ("01-01-1900", True, "01-01-1900"),
        ("31-12-2024", True, "31-12-2024"),
    ])
    def test_valid_dates(self, date_input, expected_valid, expected_normalized):
        """Test valid date inputs."""
        result = validate_birth_date(date_input)
        assert result.is_valid == expected_valid
        if expected_valid:
            assert result.normalized_value == expected_normalized
            assert result.error is None

    @pytest.mark.parametrize("date_input,error_contains", [
        # Invalid format
        ("not a date", "format"),
        ("abc", "format"),

        # Invalid day/month
        ("32-01-1990", "day"),
        ("15-13-1990", "month"),
        ("00-08-1990", "day"),
        ("15-00-1990", "month"),

        # Future dates (too far)
        ("15-08-2050", "future"),

        # Too old
        ("15-08-1800", "year"),
    ])
    def test_invalid_dates(self, date_input, error_contains):
        """Test invalid date inputs."""
        result = validate_birth_date(date_input)
        assert result.is_valid is False
        assert error_contains.lower() in result.error.lower()

    def test_empty_date(self):
        """Test empty date input."""
        result = validate_birth_date("")
        assert result.is_valid is False
        assert "required" in result.error.lower() or "empty" in result.error.lower()


class TestBirthTimeValidation:
    """Test birth time validation."""

    @pytest.mark.parametrize("time_input,expected_valid,expected_normalized", [
        # 12-hour format
        ("10:30 AM", True, "10:30 AM"),
        ("10:30 am", True, "10:30 AM"),
        ("10:30AM", True, "10:30 AM"),
        ("10:30am", True, "10:30 AM"),
        ("10:30 PM", True, "10:30 PM"),
        ("12:00 PM", True, "12:00 PM"),
        ("12:00 AM", True, "12:00 AM"),

        # 24-hour format
        ("14:30", True, "02:30 PM"),
        ("00:00", True, "12:00 AM"),
        ("23:59", True, "11:59 PM"),
        ("12:00", True, "12:00 PM"),

        # Edge times
        ("01:00 AM", True, "01:00 AM"),
        ("11:59 PM", True, "11:59 PM"),
    ])
    def test_valid_times(self, time_input, expected_valid, expected_normalized):
        """Test valid time inputs."""
        result = validate_birth_time(time_input)
        assert result.is_valid == expected_valid
        if expected_valid:
            assert result.normalized_value == expected_normalized

    @pytest.mark.parametrize("time_input,error_contains", [
        # Invalid format
        ("not a time", "format"),
        ("abc", "format"),

        # Invalid hours/minutes
        ("25:00", "hour"),
        ("13:00 AM", "hour"),
        ("10:60", "minute"),
        ("10:99 AM", "minute"),
    ])
    def test_invalid_times(self, time_input, error_contains):
        """Test invalid time inputs."""
        result = validate_birth_time(time_input)
        assert result.is_valid is False
        assert error_contains.lower() in result.error.lower()


class TestBirthPlaceValidation:
    """Test birth place validation."""

    @pytest.mark.parametrize("place_input,expected_valid", [
        # Valid places
        ("Delhi", True),
        ("New Delhi", True),
        ("Mumbai, Maharashtra", True),
        ("New York, USA", True),
        ("London", True),

        # Valid with special characters
        ("St. Louis", True),
        ("O'Brien", True),
    ])
    def test_valid_places(self, place_input, expected_valid):
        """Test valid place inputs."""
        result = validate_birth_place(place_input)
        assert result.is_valid == expected_valid

    @pytest.mark.parametrize("place_input,error_contains", [
        # Too short
        ("A", "short"),
        ("", "required"),

        # Invalid characters
        ("Delhi@123", "character"),
        ("Mumbai#$%", "character"),
    ])
    def test_invalid_places(self, place_input, error_contains):
        """Test invalid place inputs."""
        result = validate_birth_place(place_input)
        assert result.is_valid is False
        assert error_contains.lower() in result.error.lower()


class TestAllBirthDetailsValidation:
    """Test combined validation."""

    def test_all_valid_details(self, test_birth_details):
        """Test all valid birth details."""
        is_valid, normalized, errors = validate_all_birth_details(
            date=test_birth_details["date"],
            time=test_birth_details["time"],
            place=test_birth_details["place"],
        )

        assert is_valid is True
        assert "date" in normalized
        assert "time" in normalized
        assert "place" in normalized
        assert len(errors) == 0

    def test_partial_invalid_details(self):
        """Test partially invalid birth details."""
        is_valid, normalized, errors = validate_all_birth_details(
            date="invalid-date",
            time="10:30 AM",
            place="Delhi",
        )

        assert is_valid is False
        assert "date" in errors

    def test_all_invalid_details(self):
        """Test all invalid birth details."""
        is_valid, normalized, errors = validate_all_birth_details(
            date="invalid",
            time="invalid",
            place="",
        )

        assert is_valid is False
        assert len(errors) >= 2
