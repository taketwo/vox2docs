"""Command line interface for vox2docs."""

from importlib import metadata

import click

from vox2docs.daemon import Daemon
from vox2docs.logging import configure_logging, DEBUG, get_logger, INFO


logger = get_logger(__name__)


def get_version() -> str:
    """Get the package version."""
    try:
        return metadata.version("vox2docs")
    except metadata.PackageNotFoundError:
        return "unknown"


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging.",
)
@click.version_option(version=get_version(), prog_name="vox2docs")
def main(*, debug: bool = False) -> None:
    """vox2docs - Process voice recordings into transcripts and insights."""
    configure_logging(level=DEBUG if debug else INFO)


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
