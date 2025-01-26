"""Configuration management for vox2docs."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

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


class DirectoryConfig(BaseModel):
    """Configuration for the directory structure.

    All paths that are not absolute are resolved relative to the base directory.
    """

    model_config = ConfigDict(frozen=True)

    base: Path = Field(description="Base directory for vox2docs data")
    inbox: Path = Field(
        default="inbox",
        description="Directory to watch for new recordings",
    )
    recordings: Path = Field(
        default="recordings",
        description="Directory for processed recordings",
    )
    transcripts: Path = Field(
        default="transcripts",
        description="Directory for transcripts",
    )
    analysis: Path = Field(
        default="analysis",
        description="Directory for analysis outputs",
    )

    def __init__(self, **data) -> None:
        """Initialize directory config and resolve paths."""
        super().__init__(**data)
        base = self.base.expanduser().resolve()
        object.__setattr__(self, "base", base)
        for field in ["inbox", "recordings", "transcripts", "analysis"]:
            path = getattr(self, field)
            path = path.expanduser()
            if not path.is_absolute():
                object.__setattr__(self, field, (base / path).resolve())
            else:
                object.__setattr__(self, field, path.resolve())


class Config(BaseModel):
    """Application configuration.

    Attributes
    ----------
    directories : DirectoryConfig
        Configuration for the directory structure.

    """

    model_config = ConfigDict(frozen=True)

    directories: DirectoryConfig

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
            logger.exception("Failed to load config from %s", path)
            raise ConfigLoadError.from_path(path) from e
        else:
            logger.debug("Loaded configuration from %s", path)
            return config
