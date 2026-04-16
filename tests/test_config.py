"""Tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from vox2docs.config import Config, ConfigLoadError


def make_config(tmp_path: Path, extra: dict | None = None) -> Config:
    """Create a Config with base_directory set to tmp_path."""
    data = {
        "base_directory": str(tmp_path),
        "cleanup": {"llm_model": "test-model"},
        **(extra or {}),
    }
    return Config.model_validate(data)


class TestResolvePathsRelative:
    def test_monitor_input_directory_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        assert config.monitor.input_directory == tmp_path / "inbox"

    def test_rename_output_directory_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        assert config.rename.output_directory == tmp_path / "recordings"

    def test_transcribe_output_directory_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        assert config.transcribe.output_directory == tmp_path / "transcripts" / "raw"

    def test_cleanup_output_directory_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        assert config.cleanup.output_directory == tmp_path / "transcripts" / "clean"

    def test_custom_relative_path_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path, {"rename": {"output_directory": "custom/dir"}})
        assert config.rename.output_directory == tmp_path / "custom" / "dir"


class TestResolvePathsAbsolute:
    def test_absolute_path_unchanged(self, tmp_path: Path) -> None:
        absolute = tmp_path / "absolute" / "recordings"
        config = make_config(tmp_path, {"rename": {"output_directory": str(absolute)}})
        assert config.rename.output_directory == absolute

    def test_absolute_base_directory_resolved(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        assert config.base_directory == tmp_path.resolve()


class TestResolvePathsHomeExpansion:
    def test_tilde_in_base_directory_expanded(self) -> None:
        config = Config.model_validate(
            {"base_directory": "~/vox2docs", "cleanup": {"llm_model": "test-model"}}
        )
        assert not str(config.base_directory).startswith("~")
        assert config.base_directory.is_absolute()


class TestFromPath:
    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "base_directory": str(tmp_path),
                    "cleanup": {"llm_model": "test-model"},
                }
            )
        )
        config = Config.from_path(config_file)
        assert config.base_directory == tmp_path.resolve()

    def test_loads_yaml_with_custom_fields(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "base_directory": str(tmp_path),
                    "rename": {"output_directory": "custom"},
                    "cleanup": {"llm_model": "test-model"},
                }
            )
        )
        config = Config.from_path(config_file)
        assert config.rename.output_directory == tmp_path / "custom"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigLoadError):
            Config.from_path(tmp_path / "nonexistent.yaml")

    def test_raises_on_invalid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text("this: is: not: valid: yaml: [")
        with pytest.raises(ConfigLoadError):
            Config.from_path(config_file)

    def test_raises_on_missing_required_field(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"monitor": {"scan_on_startup": False}}))
        with pytest.raises(ConfigLoadError):
            Config.from_path(config_file)


class TestFromPathOrDefault:
    def test_uses_explicit_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "base_directory": str(tmp_path),
                    "cleanup": {"llm_model": "test-model"},
                }
            )
        )
        config = Config.from_path_or_default(config_file)
        assert config.base_directory == tmp_path.resolve()

    def test_uses_default_location(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        default_dir = tmp_path / ".config" / "vox2docs"
        default_dir.mkdir(parents=True)
        config_file = default_dir / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "base_directory": str(tmp_path),
                    "cleanup": {"llm_model": "test-model"},
                }
            )
        )
        monkeypatch.setenv("HOME", str(tmp_path))
        config = Config.from_path_or_default()
        assert config.base_directory == tmp_path.resolve()

    def test_raises_when_no_config_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        with pytest.raises(ConfigLoadError):
            Config.from_path_or_default()
