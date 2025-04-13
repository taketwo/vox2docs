from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Processor:
    """Base class for processors in the pipeline."""

    def __init__(self, name: str) -> None:
        """Initialize the processor."""
        self.name = name

    def process(self, input_path: Path) -> Path:
        """Process the input file and return the path to output file."""
        raise NotImplementedError
