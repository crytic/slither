"""Analysis discovery and selection for the --analyze CLI flag."""

from __future__ import annotations

from typing import List, Type

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.registry.abstract_analysis import (
    AbstractAnalysis,
)

logger = get_logger()


def get_analysis_classes() -> List[Type[AbstractAnalysis]]:
    """Return all registered analysis classes.

    Import is deferred to avoid circular imports and to allow graceful
    degradation when optional analysis modules are not installed.
    """
    classes: List[Type[AbstractAnalysis]] = []

    try:
        from slither.analyses.data_flow.analyses.rounding.output.cli import (
            RoundingCLI,
        )
        classes.append(RoundingCLI)
    except ImportError:
        pass

    return classes


def choose_analyses(
    requested: List[str],
    available: List[Type[AbstractAnalysis]],
) -> List[Type[AbstractAnalysis]]:
    """Select analyses by ARGUMENT name from the available list.

    Args:
        requested: Analysis names from --analyze CLI flag.
        available: All registered analysis classes.

    Returns:
        Matching analysis classes in the order requested.

    Raises:
        SystemExit: If a requested analysis name is not found.
    """
    lookup = {cls.ARGUMENT: cls for cls in available}
    selected: List[Type[AbstractAnalysis]] = []

    for name in requested:
        analysis_class = lookup.get(name)
        if analysis_class is None:
            known = ", ".join(sorted(lookup.keys())) or "(none)"
            logger.error(
                f"Unknown analysis: '{name}'. "
                f"Available: {known}"
            )
            raise SystemExit(1)
        selected.append(analysis_class)

    return selected
