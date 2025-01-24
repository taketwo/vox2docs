"""Command line interface for vox2docs."""

import sys
from importlib import metadata
from pathlib import Path

import click

from vox2docs.config import Config, ConfigLoadError
from vox2docs.daemon import Daemon
from vox2docs.logging import configure_logging, DEBUG, get_logger, INFO


logger = get_logger(__name__)


def get_version() -> str:
    """Get the package version."""
    try:
        return metadata.version("vox2docs")
    except metadata.PackageNotFoundError:
        return "unknown"


class State:
    """Application state holding global configuration."""

    def __init__(self) -> None:
        """Initialize the state."""
        self.config: Config | None = None


pass_state = click.make_pass_decorator(State, ensure=True)


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging.",
)
@click.version_option(version=get_version(), prog_name="vox2docs")
@pass_state
def main(state: State, *, config: Path | None, debug: bool = False) -> None:
    """vox2docs - Process voice recordings into transcripts and insights."""
    configure_logging(level=DEBUG if debug else INFO)
    try:
        state.config = Config.from_path_or_default(config)
    except ConfigLoadError:
        logger.exception()
        sys.exit(1)


@main.group()
def daemon() -> None:
    """Daemon mode operations."""


@daemon.command()
def run() -> None:
    """Run the daemon process."""
    daemon = Daemon()
    daemon.run()


if __name__ == "__main__":
    main()
