from pathlib import Path

from jinja2 import Environment, PackageLoader

from vox2docs.config import CleanupProcessorConfig
from vox2docs.processors.cleanup_processor import CleanupProcessor


def make_config(tmp_path: Path, **kwargs) -> CleanupProcessorConfig:
    data = {"llm_model": "test-model", "output_directory": str(tmp_path), **kwargs}
    return CleanupProcessorConfig.model_validate(data)


class TestPreprocess:
    def test_strips_trailing_ellipsis(self, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello...\n")
        processor = CleanupProcessor(make_config(tmp_path))
        result = processor._preprocess(input_file)
        assert result == "Hello\n"

    def test_removes_duplicate_lines(self, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello\nHello\nWorld\n")
        processor = CleanupProcessor(make_config(tmp_path))
        result = processor._preprocess(input_file)
        assert result == "Hello\nWorld\n"

    def test_keeps_intentional_non_consecutive_repeats(self, tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        input_file.write_text("Hello\nWorld\nHello\n")
        processor = CleanupProcessor(make_config(tmp_path))
        result = processor._preprocess(input_file)
        assert result == "Hello\nWorld\nHello\n"


class TestBuildPrompt:
    def _render(self, transcript: str, speaker_background: str = "") -> str:
        env = Environment(  # noqa: S701
            loader=PackageLoader("vox2docs", "resources/prompts"),
            keep_trailing_newline=True,
        )
        template = env.get_template("cleanup.j2")
        return template.render(
            speaker_background=speaker_background,
            transcript=transcript,
        )

    def test_transcript_appears_in_data_tags(self) -> None:
        result = self._render(transcript="test transcript")
        assert "<data>\ntest transcript\n</data>" in result

    def test_speaker_background_section_present_when_set(self) -> None:
        speaker_background = "Journalist from Kazakhstan, lives in New York, speaks English very nice, wife is Oksana."
        result = self._render(transcript="t", speaker_background=speaker_background)
        assert "## Speaker's Background Information" in result
        assert speaker_background in result

    def test_speaker_background_section_absent_when_empty(self) -> None:
        result = self._render(transcript="t", speaker_background="")
        assert "## Speaker's Background Information" not in result
