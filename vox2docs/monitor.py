"""File system monitoring for new files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Collection

logger = logging.getLogger(__name__)


class NewFileMonitor:
    """Monitors filesystem for new files matching given criteria.

    This class combines a filesystem observer with event handling to detect new files
    matching specified extensions. Discovered files have their paths added to a queue
    for processing.

    The monitoring is non-recursive - only the specified directory is watched, not its
    subdirectories.
    """

    def __init__(
        self,
        path: Path,
        extensions: Collection[str],
        queue: deque[Path],
        *,
        scan_on_startup: bool = True,
    ) -> None:
        """Initialize the monitor.

        Parameters
        ----------
        path : Path
            Directory path to monitor.
        extensions : Collection[str]
            File extensions (including the dot) to monitor.
        queue : deque[Path]
            Queue where paths to discovered files will be added.
        scan_on_startup : bool, default=True
            Whether to scan the directory for existing files when starting.

        Raises
        ------
        ValueError
            If path does not exist or is not a directory
            If extensions is empty
            If any extension does not start with a dot

        """
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        if not extensions:
            raise ValueError("No extensions specified")
        if any(not ext.startswith(".") for ext in extensions):
            raise ValueError("Extensions must start with a dot")

        handler = _MonitorEventHandler(path, extensions, queue)
        self.path = path
        self.extensions = extensions
        self.queue = queue
        self.scan_on_startup = scan_on_startup
        self._observer = Observer()
        self._observer.schedule(handler, str(path), recursive=False)

    def start(self) -> None:
        """Start monitoring for new files.

        The monitor will begin watching the specified directory and adding paths of new
        files to the queue. If scan_on_startup is True, existing files will be scanned
        first before starting the file watcher.
        """
        if self.scan_on_startup:
            self._scan_existing_files()

        logger.info(
            "Starting file monitoring at %s (extensions: %s)",
            self.path,
            ", ".join(sorted(self.extensions)),
        )
        self._observer.start()

    def stop(self) -> None:
        """Stop monitoring for new files.

        This method blocks until the underlying observer has completely stopped.
        """
        logger.info("Stopping file monitoring")
        self._observer.stop()
        self._observer.join()

    def _scan_existing_files(self) -> None:
        """Scan directory for existing files matching extensions and add to queue.

        This method scans the monitored directory for files that match the configured
        extensions and adds them to the processing queue. Files are validated using
        the same criteria as the event handler (non-empty, correct extension).
        """
        logger.info("Scanning for existing files in %s", self.path)

        for relative_path in self.path.iterdir():
            size = relative_path.stat().st_size
            logger.debug(
                "Found file (path: %s, size: %d bytes)",
                relative_path,
                size,
            )
            if relative_path.is_dir():
                logger.debug("Ignoring because it is directory")
                return
            if relative_path.suffix not in self.extensions:
                logger.debug("Ignoring because its extension is not monitored")
                return
            if size == 0:
                logger.debug("Ignoring because it is empty")
                return
            logger.info("Discovered new file: %s", relative_path)
            self.queue.append(self.path / relative_path)


class _MonitorEventHandler(FileSystemEventHandler):
    """Internal event handler for file system events.

    This handler filters file system events and performs validation before adding paths
    to the processing queue.
    """

    def __init__(
        self,
        path: Path,
        extensions: Collection[str],
        queue: deque[Path],
    ) -> None:
        """Initialize the event handler.

        Parameters
        ----------
        path : Path
            Directory path being monitored for reporting relative paths.
        extensions : Collection[str]
            File extensions to monitor for.
        queue : deque[Path]
            Queue where valid file paths will be added.

        """
        self.path = path
        self.extensions = extensions
        self.queue = queue

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events.

        Validates new files and adds their paths to the queue if they match the
        monitored extensions and pass basic sanity checks.

        Parameters
        ----------
        event : FileCreatedEvent
            The file creation event.

        """
        path = Path(event.src_path)
        relative_path = path.relative_to(self.path)
        size = path.stat().st_size
        logger.debug(
            "File created event (path: %s, size: %d bytes)",
            relative_path,
            size,
        )
        if event.is_directory:
            logger.debug("Ignoring because it is directory")
            return
        if path.suffix not in self.extensions:
            logger.debug("Ignoring because its extension is not monitored")
            return
        if size == 0:
            logger.debug("Ignoring because it is empty")
            return
        logger.info("Discovered new file: %s", relative_path)
        self.queue.append(path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events.

        Logs modifications to monitored files for debugging purposes.

        Parameters
        ----------
        event : FileModifiedEvent
            The file modification event.

        """
        path = Path(event.src_path)
        relative_path = path.relative_to(self.path)
        size = path.stat().st_size
        logger.debug(
            "File modified event (path: %s, size: %d bytes)",
            relative_path,
            size,
        )
