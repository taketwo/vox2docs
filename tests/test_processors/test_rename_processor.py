from datetime import datetime, UTC

import pytest

from vox2docs.processors.rename_processor import (
    InvalidFilenameError,
    RecordingInfo,
    RenameProcessor,
)


class TestParseFilename:
    """Tests for the parse_filename static method."""

    def test_valid_filename(self):
        """Test parsing a valid filename."""
        info = RenameProcessor.parse_filename("23 Aug at 10:30.m4a")
        assert info.month == 8
        assert info.day == 23
        assert info.hours == 10
        assert info.minutes == 30

    def test_different_extension(self):
        """Test parsing with a different file extension."""
        info = RenameProcessor.parse_filename("5 Dec at 23:45.wav")
        assert info.month == 12
        assert info.day == 5
        assert info.hours == 23
        assert info.minutes == 45

    def test_no_extension(self):
        """Test parsing a filename without extension."""
        info = RenameProcessor.parse_filename("1 Jan at 01:05")
        assert info.month == 1
        assert info.day == 1
        assert info.hours == 1
        assert info.minutes == 5

    def test_dash_separator(self):
        """Test parsing when dash is used as separator."""
        info = RenameProcessor.parse_filename("15 Jul at 20-45.wav")
        assert info.month == 7
        assert info.day == 15
        assert info.hours == 20
        assert info.minutes == 45

    def test_invalid_format(self):
        """Test parsing an invalid filename format."""
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("invalid-filename.m4a")
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("23 Aug 10:30.m4a")
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("23 Aug at 1030.m4a")

    def test_unknown_month(self):
        """Test parsing unknown month name."""
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("23 Xyz at 10:30.m4a")


@pytest.fixture
def fixed_datetime():
    """Return a fixed datetime for testing (Wednesday 2025-04-09 15:30 UTC)."""
    return datetime(2025, 4, 9, 15, 30, 0, tzinfo=UTC)


class TestFindMatchingDate:
    """Tests for the find_matching_date static method."""

    def test_same_date(self, fixed_datetime):
        """Test finding a date for the same date as the reference time."""
        info = RecordingInfo(month=4, day=9, hours=10, minutes=30)  # April 9
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        assert result.date() == fixed_datetime.date()
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
        assert result.microsecond == 0

    def test_past_date_same_year(self, fixed_datetime):
        """Test finding a date earlier in the same year."""
        info = RecordingInfo(month=3, day=15, hours=8, minutes=15)  # March 15
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        assert result.year == fixed_datetime.year
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 8
        assert result.minute == 15
        assert result.second == 0
        assert result.microsecond == 0

    def test_future_date_wraps_to_previous_year(self, fixed_datetime):
        """Test that a future date resolves to previous year."""
        info = RecordingInfo(month=12, day=25, hours=9, minutes=0)  # December 25
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        assert result.year == fixed_datetime.year - 1
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 9
        assert result.minute == 0

    def test_time_in_future_same_date(self, fixed_datetime):
        """Test handling when recording time is in the future on the same date."""
        info = RecordingInfo(month=4, day=9, hours=16, minutes=0)  # April 9, 16:00
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        assert result.year == fixed_datetime.year - 1
        assert result.month == 4
        assert result.day == 9
        assert result.hour == 16
        assert result.minute == 0
