"""Configuration management for vox2docs."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from vox2docs.logging import get_logger

logger = get_logger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded from a file."""

    @classmethod
    def from_path(cls, path: Path) -> ConfigLoadError:
        """Create error for failed load from specific path."""
        return cls(f"Could not load config from {path}")

    @classmethod
    def no_config_found(cls) -> ConfigLoadError:
        """Create error for when no config file can be found."""
        return cls("No config file found")


class MonitorConfig(BaseModel):
    """Configuration for the file monitor."""

    model_config = ConfigDict(frozen=True)

    input_directory: Path = Field(
        default="inbox",
        description="Directory to watch for new recordings",
    )
    extensions: set[str] = Field(
        default_factory=lambda: {".m4a"},
        description="File extensions to monitor",
    )


class RenameProcessorConfig(BaseModel):
    """Configuration for the rename processor."""

    model_config = ConfigDict(frozen=True)

    output_directory: Path = Field(
        default="recordings",
        description="Directory for processor output",
    )


class TranscribeProcessorConfig(BaseModel):
    """Configuration for the transcribe processor."""

    model_config = ConfigDict(frozen=True)

    output_directory: Path = Field(
        default="transcripts/raw",
        description="Directory for processor output",
    )


class Config(BaseModel):
    """Application configuration."""

    model_config = ConfigDict(validate_assignment=True, frozen=False)

    base_directory: Path = Field(
        description="Base directory for vox2docs data",
    )
    monitor: MonitorConfig = Field(
        default_factory=MonitorConfig,
        description="File monitor configuration",
    )
    rename: RenameProcessorConfig = Field(
        default_factory=RenameProcessorConfig,
        description="Rename processor configuration",
    )
    transcribe: TranscribeProcessorConfig = Field(
        default_factory=TranscribeProcessorConfig,
        description="Transcribe processor configuration",
    )

    @classmethod
    def from_path_or_default(cls, path: Path | None = None) -> Config:
        """Create configuration from a file, falling back to default location.

        Parameters
        ----------
        path : Path | None
            Path to configuration file. If None, tries default location.

        Returns
        -------
        Config
            Loaded configuration

        Raises
        ------
        ConfigLoadError
            If configuration cannot be loaded from either path.

        """
        if path:
            return cls.from_path(path)

        default_path = Path.home() / ".config" / "vox2docs" / "config.yaml"
        if default_path.is_file():
            return cls.from_path(default_path)

        raise ConfigLoadError.no_config_found()

    @classmethod
    def from_path(cls, path: Path) -> Config:
        """Create configuration from a file.

        Parameters
        ----------
        path : Path
            Path to configuration file.

        Returns
        -------
        Config
            Loaded configuration.

        Raises
        ------
        ConfigLoadError
            If file cannot be read or parsed.

        """
        try:
            with path.open() as f:
                data = yaml.safe_load(f)
            config = cls.model_validate(data)
        except Exception as e:
            raise ConfigLoadError.from_path(path) from e
        else:
            logger.debug("Loaded configuration from %s", path)
            return config

    @model_validator(mode="after")
    def resolve_paths(self) -> Config:
        """Resolve relative paths in the configuration.

        This validator processes Path objects in config fields to ensure consistent path
        handling throughout the application. It:

        1. Resolves base_directory to its absolute form
        2. For each processor config (BaseModel instance):
            - Identifies fields annotated as Path
            - Converts any string values to Path objects
            - Resolves relative paths against base_directory
            - Leaves absolute paths unchanged

        Note: we have to use object.__setattr__ to avoid triggering nested validation
        loops when updating path values.

        Returns
        -------
        Config
            Updated configuration with resolved paths

        """
        object.__setattr__(
            self,
            "base_directory",
            self.base_directory.expanduser().resolve(),
        )

        for field_value in self.__dict__.values():
            if isinstance(field_value, BaseModel):
                model_fields = field_value.__class__.model_fields
                for subfield_name, subfield_value in field_value.__dict__.items():
                    if (
                        subfield_name in model_fields
                        and model_fields[subfield_name].annotation == Path
                    ):
                        resolved_path = Path(subfield_value)
                        if not resolved_path.is_absolute():
                            resolved_path = (
                                self.base_directory / resolved_path
                            ).resolve()
                        object.__setattr__(
                            field_value,
                            subfield_name,
                            resolved_path,
                        )

        return self
