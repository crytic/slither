"""Analysis discovery and selection for the --analyze CLI flag."""

from __future__ import annotations

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.registry.abstract_analysis import (
    AbstractAnalysis,
)

logger = get_logger()

try:
    from slither.analyses.data_flow.analyses.rounding.output.cli import (
        RoundingCLI,
    )
    _ROUNDING_AVAILABLE = True
except ImportError:
    _ROUNDING_AVAILABLE = False


def get_analysis_classes() -> list[type[AbstractAnalysis]]:
    """Return all registered analysis classes."""
    classes: list[type[AbstractAnalysis]] = []
    if _ROUNDING_AVAILABLE:
        classes.append(RoundingCLI)
    return classes


def choose_analyses(
    requested: list[str],
    available: list[type[AbstractAnalysis]],
) -> list[type[AbstractAnalysis]]:
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
    selected: list[type[AbstractAnalysis]] = []

    for name in requested:
        analysis_class = lookup.get(name)
        if analysis_class is None:
            known = ", ".join(sorted(lookup.keys())) or "(none)"
            logger.error(
                "Unknown analysis: '{name}'. Available: {known}",
                name=name,
                known=known,
            )
            raise SystemExit(1)
        selected.append(analysis_class)

    return selected
