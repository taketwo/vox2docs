from __future__ import annotations

import contextlib
import ctypes
import sysconfig
from pathlib import Path
from typing import TYPE_CHECKING

from faster_whisper import WhisperModel

from vox2docs.logging import get_logger
from vox2docs.processors.processor import Processor

if TYPE_CHECKING:
    from vox2docs.config import TranscribeProcessorConfig

logger = get_logger(__name__)


class TranscribeProcessor(Processor):
    """Transcribes audio recordings into text."""

    def __init__(self, config: TranscribeProcessorConfig) -> None:
        """Initialize the transcribe processor."""
        super().__init__(name="transcribe")
        self.config = config

    def process(self, input_path: Path) -> Path:
        """Transcribe the audio file and save the transcript."""
        transcript_path = self.config.output_directory / (input_path.stem + ".txt")
        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        _preload_nvidia_libs()
        model = WhisperModel(
            self.config.model_size,
            device=self.config.device,
            compute_type=self.config.compute_type,
        )
        segments, info = model.transcribe(
            str(input_path),
            beam_size=5,
            vad_filter=self.config.vad_filter,
            vad_parameters={
                "min_silence_duration_ms": self.config.vad_min_silence_duration_ms,
            },
        )
        logger.info(
            "Detected language '%s' with probability %.2f",
            info.language,
            info.language_probability,
        )

        with transcript_path.open("w") as f:
            for segment in segments:
                f.write(f"{segment.text}\n")

        return transcript_path


def _preload_nvidia_libs() -> None:
    """Preload nvidia shared libs so ctranslate2 can find them without LD_LIBRARY_PATH."""
    site = Path(sysconfig.get_path("purelib"))
    for so in sorted(site.glob("nvidia/*/lib/lib*.so*")):
        if not so.is_symlink():
            with contextlib.suppress(OSError):
                ctypes.CDLL(str(so))
