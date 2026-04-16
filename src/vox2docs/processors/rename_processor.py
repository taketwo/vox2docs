from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from vox2docs.logging import get_logger
from vox2docs.processors.processor import Processor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import RenameProcessorConfig


logger = get_logger(__name__)


class InvalidFilenameError(Exception):
    """Raised when a filename does not match the expected format."""

    @classmethod
    def unexpected_format(cls, filename: str) -> InvalidFilenameError:
        """Create error for unexpected filename format."""
        return cls(f"Filename '{filename}' does not match expected format")

    @classmethod
    def unknown_month(cls, month: str) -> InvalidFilenameError:
        """Create error for unknown month in filename."""
        return cls(f"Unknown month '{month}' in filename")


@dataclass
class RecordingInfo:
    """Information extracted from a recording filename."""

    month: int
    day: int
    hours: int
    minutes: int


class RenameProcessor(Processor):
    """Renames and organizes recording files."""

    def __init__(self, config: RenameProcessorConfig) -> None:
        super().__init__(name="rename")
        self.config = config

    def process(self, input_path: Path) -> Path:
        """Process the recording file.

        Parameters
        ----------
        input_path : Path
            Path to the input file

        Returns
        -------
        Path
            Path to the renamed file

        Raises
        ------
        InvalidFilenameError
            If the filename doesn't match the expected format

        """
        local_tz = datetime.now().astimezone().tzinfo
        reference_time = datetime.fromtimestamp(input_path.stat().st_mtime, tz=local_tz)

        logger.debug("Last modified time of %s: %s", input_path, reference_time)

        recording_info = self.parse_filename(input_path.name)
        recording_datetime = self.find_matching_date(recording_info, reference_time)

        formatted_date = recording_datetime.strftime("%Y-%m-%d-%H-%M")
        extension = input_path.suffix
        output_filename = f"{formatted_date}{extension}"

        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_directory / output_filename

        logger.debug("Copying %s to %s", input_path.name, output_filename)
        shutil.copy2(input_path, output_path)

        return output_path

    @staticmethod
    def parse_filename(filename: str) -> RecordingInfo:
        """Parse filename to extract recording information.

        Parameters
        ----------
        filename : str
            The filename to parse

        Returns
        -------
        RecordingInfo
            Extracted recording information

        Raises
        ------
        InvalidFilenameError
            If the filename doesn't match the expected format

        """
        regex = re.compile(
            r"^(?P<day>\d{1,2}) (?P<month>\w+) at (?P<hours>\d{2})[:-](?P<minutes>\d{2})(?:\..*)?$",
        )
        match = regex.match(filename)
        if not match:
            raise InvalidFilenameError.unexpected_format(filename)

        month_name = match.group("month")
        try:
            month_index = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sept",
                "Oct",
                "Nov",
                "Dec",
            ].index(month_name) + 1
        except ValueError as e:
            raise InvalidFilenameError.unknown_month(month_name) from e

        day = int(match.group("day"))
        hours = int(match.group("hours"))
        minutes = int(match.group("minutes"))

        logger.debug(
            "Parsed filename '%s' into month: %d, day: %d, hours: %d, minutes: %d",
            filename,
            month_index,
            day,
            hours,
            minutes,
        )

        return RecordingInfo(month=month_index, day=day, hours=hours, minutes=minutes)

    @staticmethod
    def find_matching_date(
        recording_info: RecordingInfo,
        reference_time: datetime,
    ) -> datetime:
        """Find the date of the most recent occurrence of the given month/day and time.

        This method determines the most recent date that matches the month, day and time
        in the recording_info and is not in the future relative to reference_time. It
        handles year boundaries by checking both current and previous year.

        Parameters
        ----------
        recording_info : RecordingInfo
            Recording information containing the month, day, hours and minutes
        reference_time : datetime
            Reference time to calculate from

        Returns
        -------
        datetime
            Date of the most recent occurrence of the month/day and time

        """
        # Try current year first
        try:
            candidate_time = reference_time.replace(
                month=recording_info.month,
                day=recording_info.day,
                hour=recording_info.hours,
                minute=recording_info.minutes,
                second=0,
                microsecond=0,
            )
        except ValueError:
            # Invalid date (e.g., Feb 29 in non-leap year), try previous year
            candidate_time = reference_time.replace(
                year=reference_time.year - 1,
                month=recording_info.month,
                day=recording_info.day,
                hour=recording_info.hours,
                minute=recording_info.minutes,
                second=0,
                microsecond=0,
            )

        # If candidate is in the future, use previous year's occurrence
        if candidate_time > reference_time:
            candidate_time = candidate_time.replace(year=candidate_time.year - 1)

        return candidate_time
