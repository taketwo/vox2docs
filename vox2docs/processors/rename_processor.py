from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
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
    def unknown_weekday(cls, weekday: str) -> InvalidFilenameError:
        """Create error for unknown weekday in filename."""
        return cls(f"Unknown weekday '{weekday}' in filename")


@dataclass
class RecordingInfo:
    """Information extracted from a recording filename."""

    weekday_index: int
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

        import shutil

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
            r"^(?P<weekday>\w+) at (?P<hours>\d{2})[:-](?P<minutes>\d{2})(?:\..*)?$",
        )
        match = regex.match(filename)
        if not match:
            raise InvalidFilenameError.unexpected_format(filename)

        weekday_name = match.group("weekday")
        try:
            weekday_index = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ].index(weekday_name)
        except ValueError as e:
            raise InvalidFilenameError.unknown_weekday(weekday_name) from e

        hours = int(match.group("hours"))
        minutes = int(match.group("minutes"))

        logger.debug(
            "Parsed filename '%s' into weekday: %d, hours: %d, minute:s %d",
            filename,
            weekday_index,
            hours,
            minutes,
        )

        return RecordingInfo(weekday_index=weekday_index, hours=hours, minutes=minutes)

    @staticmethod
    def find_matching_date(
        recording_info: RecordingInfo,
        reference_time: datetime,
    ) -> datetime:
        """Find the date of the most recent occurrence of the given weekday and time.

        This method determines the most recent date that matches the weekday and time
        in the recording_info and is not in the future relative to reference_time. It
        starts from the reference time and steps backward one day at a time until
        finding the first matching weekday.

        Parameters
        ----------
        recording_info : RecordingInfo
            Recording information containing the weekday index
        reference_time : datetime
            Reference time to calculate from

        Returns
        -------
        datetime
            Date of the most recent occurrence of the weekday

        """
        candidate_time = reference_time.replace(
            hour=recording_info.hours,
            minute=recording_info.minutes,
            second=0,
            microsecond=0,
        )

        while (
            candidate_time > reference_time
            or candidate_time.weekday() != recording_info.weekday_index
        ):
            candidate_time -= timedelta(days=1)

        return candidate_time
