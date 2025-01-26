"""Daemon implementation for vox2docs."""

from __future__ import annotations

import signal
import time
from collections import deque
from typing import TYPE_CHECKING

from vox2docs.logging import get_logger
from vox2docs.monitor import NewFileMonitor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import Config

logger = get_logger(__name__)


class Daemon:
    """Main daemon class that handles file watching and signal management."""

    def __init__(self, config: Config) -> None:
        """Initialize the daemon."""
        logger.info("Initializing vox2docs daemon")
        self.config = config
        self.pending: deque[Path] = deque()
        self.monitor = NewFileMonitor(
            path=config.directories.inbox,
            extensions={".m4a"},  # TODO: Move to config
            queue=self.pending,
        )
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
        self.monitor.start()

        try:
            while True:
                if self.pending:
                    path = self.pending.popleft()
                    try:
                        # TODO: Replace print with actual processing
                        logger.info("Would process %s", path)
                    except Exception:
                        logger.exception("Failed to process %s", path)
                time.sleep(1)
        except SystemExit:
            logger.info("Shutting down daemon...")
            self.monitor.stop()
            if self.pending:
                logger.warning("%d files remain unprocessed", len(self.pending))
            logger.info("Daemon stopped cleanly")
