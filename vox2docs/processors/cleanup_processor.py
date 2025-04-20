from __future__ import annotations

from typing import TYPE_CHECKING

from vox2docs.processors.processor import Processor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import CleanupProcessorConfig


class CleanupProcessor(Processor):
    """Cleans up transcripts by removing unwanted characters and formatting."""

    def __init__(self, config: CleanupProcessorConfig) -> None:
        """Initialize the cleanup processor."""
        super().__init__(name="cleanup")
        self.config = config

    def process(self, input_path: Path) -> Path:
        """Clean up the transcript file and save the cleaned version."""
        output_path = self.config.output_directory / input_path.name
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        # TODO: Replace this placeholder with actual cleanup logic
        with output_path.open("w") as f:
            f.write("Cleaned up content of " + str(input_path))
        return output_path
