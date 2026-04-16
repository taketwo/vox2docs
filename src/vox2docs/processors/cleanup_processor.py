from __future__ import annotations

from typing import TYPE_CHECKING

import llm
from jinja2 import Environment, PackageLoader

from vox2docs.processors.processor import Processor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import CleanupProcessorConfig

_SYSTEM_PROMPT = "You are an expert transcript editor specializing in cleaning up speech-to-text output."


class CleanupProcessor(Processor):
    """Cleans up transcripts using an LLM after basic pre-processing."""

    def __init__(self, config: CleanupProcessorConfig) -> None:
        """Initialize the cleanup processor."""
        super().__init__(name="cleanup")
        self.config = config
        self._env = Environment(  # noqa: S701
            loader=PackageLoader("vox2docs", "resources/prompts"),
            keep_trailing_newline=True,
        )

    def process(self, input_path: Path) -> Path:
        """Clean up the transcript file and save the cleaned version."""
        output_path = self.config.output_directory / input_path.name
        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        transcript = self._preprocess(input_path)
        cleaned = self._llm_cleanup(transcript)

        output_path.write_text(cleaned)
        return output_path

    def _preprocess(self, input_path: Path) -> str:
        """Remove obvious ASR artifacts before sending to the LLM."""
        lines: list[str] = []
        previous_line = ""
        for line in input_path.open("r"):
            cleaned_line = line.strip().removesuffix("...") + "\n"
            if cleaned_line != previous_line:
                lines.append(cleaned_line)
                previous_line = cleaned_line
        return "".join(lines)

    def _llm_cleanup(self, transcript: str) -> str:
        """Send the pre-processed transcript to the LLM for cleanup."""
        template = self._env.get_template("cleanup.j2")
        user_prompt = template.render(
            speaker_background=self.config.speaker_background,
            transcript=transcript,
        )
        model = llm.get_model(self.config.llm_model)
        response = model.prompt(user_prompt, system=_SYSTEM_PROMPT)
        return response.text()
