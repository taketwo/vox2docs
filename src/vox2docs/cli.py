"""Command line interface for vox2docs."""

import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import click
from rich.console import Console
from rich.pretty import Pretty

from vox2docs.config import Config, ConfigLoadError
from vox2docs.daemon import Daemon
from vox2docs.logging import DEBUG, INFO, configure_logging, get_logger
from vox2docs.processors.cleanup_processor import CleanupProcessor
from vox2docs.processors.rename_processor import InvalidFilenameError, RenameProcessor
from vox2docs.processors.transcribe_processor import TranscribeProcessor

_SERVICE_NAME = "vox2docs"
_UNIT_DIR = Path.home() / ".config" / "systemd" / "user"
_UNIT_FILE = _UNIT_DIR / f"{_SERVICE_NAME}.service"

logger = get_logger(__name__)


def get_version() -> str:
    """Get the package version."""
    try:
        return metadata.version("vox2docs")
    except metadata.PackageNotFoundError:
        return "unknown"


class State:
    """Application state holding global configuration."""

    config: Config


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
        logger.exception("Failed to load application config")
        sys.exit(1)


@main.group()
def daemon() -> None:
    """Daemon mode operations."""


@daemon.command()
@pass_state
def run(state: State) -> None:
    """Run the daemon process."""
    if state.config is None:
        raise RuntimeError("Config is not loaded")
    daemon_instance = Daemon(state.config)
    daemon_instance.run()


@daemon.command()
def install() -> None:
    """Install and start the systemd user service."""
    executable = sys.argv[0]

    unit_content = f"""\
[Unit]
Description=vox2docs daemon
After=network.target

[Service]
Type=simple
ExecStart={executable} --debug daemon run
Restart=on-failure

[Install]
WantedBy=default.target
"""

    _UNIT_DIR.mkdir(parents=True, exist_ok=True)
    _UNIT_FILE.write_text(unit_content)
    click.echo(f"Wrote unit file: {_UNIT_FILE}")

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "--user", "enable", "--now", _SERVICE_NAME], check=True
    )
    click.echo("Service installed and started")


@daemon.command()
def uninstall() -> None:
    """Stop, disable, and remove the systemd user service."""
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", _SERVICE_NAME], check=False
    )
    if _UNIT_FILE.exists():
        _UNIT_FILE.unlink()
        click.echo(f"Removed unit file: {_UNIT_FILE}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    click.echo("Service uninstalled")


@daemon.command()
def status() -> None:
    """Show the status of the systemd user service."""
    result = subprocess.run(
        ["systemctl", "--user", "status", _SERVICE_NAME],
        check=False,
    )
    sys.exit(result.returncode)


@daemon.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("journalctl_args", nargs=-1, type=click.UNPROCESSED)
def logs(journalctl_args: tuple[str, ...]) -> None:
    """Show logs for the systemd user service (passes args to journalctl)."""
    os.execvp(
        "journalctl",
        ["journalctl", "--user", "-u", _SERVICE_NAME, *journalctl_args],
    )


@main.group()
def config() -> None:
    """Config management operations."""


@config.command()
@pass_state
def show(state: State) -> None:
    """Display the loaded config."""
    Console().print(
        Pretty(
            state.config,
            expand_all=True,
        ),
    )


@main.group()
def step() -> None:
    """Run a single processing step on a file."""


@step.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@pass_state
def rename(state: State, *, file: Path) -> None:
    """Run the rename step on a recording file."""
    try:
        output = RenameProcessor(state.config.rename).process(file)
    except InvalidFilenameError as e:
        logger.error("Cannot rename %s: %s", file.name, e)  # noqa: TRY400
        sys.exit(1)
    click.echo(output)


@step.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@pass_state
def transcribe(state: State, *, file: Path) -> None:
    """Run the transcribe step on a recording file."""
    output = TranscribeProcessor(state.config.transcribe).process(file)
    click.echo(output)


@step.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@pass_state
def cleanup(state: State, *, file: Path) -> None:
    """Run the cleanup step on a transcript file."""
    output = CleanupProcessor(state.config.cleanup).process(file)
    click.echo(output)


if __name__ == "__main__":
    main()
