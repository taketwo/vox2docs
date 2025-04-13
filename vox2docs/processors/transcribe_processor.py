from __future__ import annotations

from typing import TYPE_CHECKING

from vox2docs.processors.processor import Processor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import TranscribeProcessorConfig


class TranscribeProcessor(Processor):
    """Transcribes audio recordings into text."""

    def __init__(self, config: TranscribeProcessorConfig) -> None:
        """Initialize the transcribe processor."""
        super().__init__(name="transcribe")
        self.config = config

    def process(self, input_path: Path) -> Path:
        """Transcribe the audio file and save the transcript."""
        # TODO: Replace this placeholder with actual transcription logic
        transcript_path = self.config.output_directory / (input_path.stem + ".txt")
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        with transcript_path.open("w") as f:
            f.write("Transcription of " + str(input_path))
        return transcript_path
