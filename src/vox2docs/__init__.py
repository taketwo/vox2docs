"""Voice recording processing system."""

from importlib import metadata

try:
    __version__ = metadata.version("vox2docs")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
