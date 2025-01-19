"""Logging configuration for vox2docs.

This module provides centralized logging configuration, adapting the output format and
behavior based on whether the application is running in an interactive or
non-interactive context.
"""

import logging
import sys
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

# Re-export logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class InteractiveLogHandler(RichHandler):
    """Enhanced RichHandler for interactive output.

    Provides rich formatting, colored output, and enhanced tracebacks suitable for
    terminal interaction.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the handler with rich formatting options.

        Parameters
        ----------
        *args : Any
            Positional arguments passed to RichHandler
        **kwargs : Any
            Keyword arguments passed to RichHandler

        """
        super().__init__(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            console=Console(stderr=True),
            *args,
            **kwargs,
        )


class NonInteractiveLogHandler(logging.StreamHandler):
    """Simplified handler for non-interactive operation.

    Provides clean, parseable output suitable for log collection systems and file
    logging.
    """

    def __init__(self) -> None:
        """Initialize the handler with a basic formatter."""
        super().__init__(sys.stdout)
        self.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ),
        )


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging behavior.

    Parameters
    ----------
    level : int, optional
        The logging level to use, by default logging.INFO

    """
    # Remove any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set basic configuration
    root_logger.setLevel(level)

    # Add appropriate handler based on environment
    if sys.stdout.isatty() and sys.stderr.isatty():
        handler = InteractiveLogHandler(markup=True)
    else:
        handler = NonInteractiveLogHandler()

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    This is a convenience wrapper around logging.getLogger that ensures consistent
    logger naming throughout the application.

    Parameters
    ----------
    name : str
        The logger name, typically __name__ from the calling module

    Returns
    -------
    logging.Logger
        A configured logger instance with appropriate namespace

    """
    if name.startswith("vox2docs."):
        return logging.getLogger(name)
    return logging.getLogger(f"vox2docs.{name}")
