"""Command line interface for vox2docs."""

from importlib import metadata

import click


def get_version() -> str:
    """Get the package version."""
    try:
        return metadata.version("vox2docs")
    except metadata.PackageNotFoundError:
        return "unknown"


@click.group()
@click.version_option(version=get_version(), prog_name="vox2docs")
def main() -> None:
    """vox2docs - Process voice recordings into transcripts and insights."""


if __name__ == "__main__":
    main()
