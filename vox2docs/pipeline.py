"""Processing pipeline for voice recordings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vox2docs.logging import get_logger
from vox2docs.processors import create_processor

if TYPE_CHECKING:
    from pathlib import Path

    from vox2docs.config import Config
    from vox2docs.processors import Processor


logger = get_logger(__name__)


class PipelineExecutionError(Exception):
    """Raised when an error occurs during pipeline execution."""

    @classmethod
    def from_processor(cls, processor_name: str) -> PipelineExecutionError:
        """Create error from specific processor."""
        return cls(f"Error in {processor_name} processor")


class Pipeline:
    """Processing pipeline for voice recordings."""

    def __init__(self, processors: list[Processor]) -> None:
        """Initialize the pipeline with a list of processors."""
        self.processors = processors

    @classmethod
    def from_config(cls, config: Config) -> Pipeline:
        """Create a pipeline from a configuration object."""
        return cls(
            [
                create_processor(config.rename),
            ],
        )

    def process(self, input_path: Path) -> None:
        """Run the processing pipeline on the given input file path."""
        logger.info("Starting pipeline for %s", input_path)
        for processor in self.processors:
            try:
                logger.info("Processing with %s processor", processor.name)
                input_path = processor.process(input_path)
            except Exception as e:
                raise PipelineExecutionError.from_processor(processor.name) from e
