"""Daemon implementation for vox2docs."""

from __future__ import annotations

import signal
import time
from collections import deque
from typing import TYPE_CHECKING

from vox2docs.logging import get_logger
from vox2docs.monitor import NewFileMonitor
from vox2docs.pipeline import Pipeline, PipelineExecutionError

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
            path=config.monitor.input_directory,
            extensions=config.monitor.extensions,
            queue=self.pending,
            scan_on_startup=config.monitor.scan_on_startup,
        )
        self.pipeline = Pipeline.from_config(config)
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
                    logger.debug("Processing queue has %d file(s)", len(self.pending))
                    path = self.pending.popleft()
                    logger.debug("Picked %s for processing", path)
                    try:
                        self.pipeline.process(path)
                        logger.info(
                            "Finished processing %s, removing original file from input directory",
                            path,
                        )
                        path.unlink()
                    except PipelineExecutionError:
                        logger.exception(
                            "Pipeline execution failed for %s; file remains in input directory",
                            path,
                        )
                time.sleep(1)
        except SystemExit:
            logger.info("Shutting down daemon...")
            self.monitor.stop()
            if self.pending:
                logger.warning("%d files remain unprocessed", len(self.pending))
            logger.info("Daemon stopped cleanly")
