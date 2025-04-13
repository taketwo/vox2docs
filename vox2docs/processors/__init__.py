"""Processors module for vox2docs.

This package provides processor classes that transform documents within the vox2docs
system. It includes a base Processor class, specific implementations like
RenameProcessor, and a factory function to create processor instances based on
configuration objects.
"""

from typing import Any

from vox2docs.processors.processor import Processor
from vox2docs.processors.rename_processor import RenameProcessor
from vox2docs.processors.transcribe_processor import TranscribeProcessor


def create_processor(config: Any) -> Processor:  # noqa: ANN401
    """Create a processor instance based on a given configuration object.

    This factory function dynamically instantiates processor classes by following a
    naming convention. It expects configuration classes to be named with the pattern
    '<Name>ProcessorConfig' and corresponding processor classes to be named
    '<Name>Processor'. The processor class must be imported and available in the
    module's global namespace.

    Parameters
    ----------
    config : Any
        A configuration object whose class name follows the '<Name>ProcessorConfig'
        pattern. This object will be passed to the processor's constructor.

    Returns
    -------
    Processor
        An instance of the appropriate processor class initialized with the provided
        configuration object.

    Raises
    ------
    ValueError
        If the config class name doesn't follow the '<Name>ProcessorConfig' naming
        convention or if a processor  class with the corresponding name is not found in
        the current module's globals.

    Notes
    -----
    All processor classes must be imported at the module level for this factory function
    to find them.

    """
    config_name = type(config).__name__
    if not config_name.endswith("ProcessorConfig"):
        raise ValueError(
            f"Config class name must end with 'ProcessorConfig': {config_name}",
        )

    processor_name = config_name[:-6]
    try:
        return globals()[processor_name](config)
    except KeyError:
        raise ValueError(
            f"Processor class '{processor_name}' not found for config type: {config_name}",
        )


__all__ = [
    "Processor",
    "RenameProcessor",
    "TranscribeProcessor",
    "create_processor",
]
