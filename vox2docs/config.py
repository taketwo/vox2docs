"""Configuration management for vox2docs."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

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


class Config(BaseModel):
    """Application configuration.

    Attributes
    ----------
    input_path : Path
        Path to watch for new recordings.

    """

    model_config = ConfigDict(frozen=True)

    input_path: Path

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
