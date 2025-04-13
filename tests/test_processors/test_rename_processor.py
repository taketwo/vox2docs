from datetime import datetime, timedelta, UTC

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
        info = RenameProcessor.parse_filename("Monday at 10:30.m4a")
        assert info.weekday_index == 0
        assert info.hours == 10
        assert info.minutes == 30

    def test_different_extension(self):
        """Test parsing with a different file extension."""
        info = RenameProcessor.parse_filename("Tuesday at 23:45.wav")
        assert info.weekday_index == 1
        assert info.hours == 23
        assert info.minutes == 45

    def test_no_extension(self):
        """Test parsing a filename without extension."""
        info = RenameProcessor.parse_filename("Wednesday at 01:05")
        assert info.weekday_index == 2
        assert info.hours == 1
        assert info.minutes == 5

    def test_invalid_format(self):
        """Test parsing an invalid filename format."""
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("invalid-filename.m4a")
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("Monday 10:30.m4a")
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("Monday at 10-30.m4a")

    def test_unknown_weekday(self):
        """Test parsing unknown weekday name."""
        with pytest.raises(InvalidFilenameError):
            RenameProcessor.parse_filename("Invaliday at 10:30.m4a")


@pytest.fixture
def fixed_datetime():
    """Return a fixed datetime for testing (Wednesday 2025-04-09 15:30 UTC)."""
    return datetime(2025, 4, 9, 15, 30, 0, tzinfo=UTC)


class TestFindMatchingDate:
    """Tests for the find_matching_date static method."""

    def test_same_weekday(self, fixed_datetime):
        """Test finding a date for the same weekday as the reference time."""
        info = RecordingInfo(weekday_index=2, hours=10, minutes=30)  # Wednesday
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        assert result.date() == fixed_datetime.date()
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
        assert result.microsecond == 0

    def test_previous_day(self, fixed_datetime):
        """Test finding a date for the previous day."""
        info = RecordingInfo(weekday_index=1, hours=8, minutes=15)
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        expected_date = (fixed_datetime - timedelta(days=1)).date()
        assert result.date() == expected_date
        assert result.hour == 8
        assert result.minute == 15
        assert result.second == 0
        assert result.microsecond == 0

    def test_future_day_wraps_to_previous_week(self, fixed_datetime):
        """Test that a 'future' weekday resolves to previous week."""
        info = RecordingInfo(weekday_index=4, hours=9, minutes=0)
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        expected_date = (fixed_datetime - timedelta(days=5)).date()
        assert result.date() == expected_date
        assert result.hour == 9
        assert result.minute == 0

    def test_time_in_future_same_day(self, fixed_datetime):
        """Test handling when recording time is in the future on the same day."""
        info = RecordingInfo(weekday_index=2, hours=16, minutes=0)
        result = RenameProcessor.find_matching_date(info, fixed_datetime)
        expected_date = (fixed_datetime - timedelta(days=7)).date()
        assert result.date() == expected_date
        assert result.hour == 16
        assert result.minute == 0
