"""Daemon implementation for vox2docs."""

from __future__ import annotations

import logging
import signal

import sys

import time

from watchdog.observers import Observer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


class Daemon:
    """Main daemon class that handles file watching and signal management."""

    def __init__(self) -> None:
        """Initialize the daemon."""
        logger.info("Initializing vox2docs daemon")
        self.observer = Observer()
        signal.signal(signal.SIGTERM, self._handle_termination)
        signal.signal(signal.SIGINT, self._handle_termination)

    def _handle_termination(
        self,
        signum: int,
        frame: object | None,  # noqa: ARG002
    ) -> None:
        """Handle termination signals."""
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info("Received %s signal", sig_name)
        raise SystemExit(0)

    def run(self) -> None:
        """Run the daemon."""
        logger.info("Starting file watching")

        # TODO: Initialize and start watchdog observer

        try:
            # TODO: Instead of endless loop, wait for the observer to stop
            while True:
                time.sleep(1)
        except SystemExit:
            logger.info("Shutting down daemon...")
            logger.info("Daemon stopped cleanly")
