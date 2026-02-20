"""Base class for configurable data-flow analyses.

Analyses are a third extension point alongside detectors and printers.
They support per-analysis CLI flags, Rich display output, and structured
serialization for JSON output and external tools like MCP servers.

Usage (CLI)::

    slither target.sol --analyze rounding --rounding-trace DOWN

Usage (programmatic)::

    analysis = RoundingCLI(known_tags=load_known_tags())
    analysis.run(slither)
    results = analysis.serialize()
"""

from __future__ import annotations

import abc
import argparse
from typing import ClassVar, Generic, List, TypeVar

from slither.core.slither_core import SlitherCore

T = TypeVar("T")


class AbstractAnalysis(abc.ABC, Generic[T]):
    """Base class for data-flow analyses with CLI and programmatic access.

    Subclasses must define ARGUMENT and HELP class variables, and implement
    from_args, run, display, and serialize methods.

    The type parameter T is the serialized result type (a TypedDict defined
    by each concrete analysis). Configuration flows through __init__ for
    programmatic use (MCP, tests) or through from_args for CLI use.
    """

    ARGUMENT: ClassVar[str]
    HELP: ClassVar[str]

    @classmethod
    def register_arguments(
        cls,
        group: argparse._ArgumentGroup,
    ) -> None:
        """Register analysis-specific CLI flags on the provided group.

        Override this to add flags like --rounding-trace, --taint-sources.
        The group is pre-created by the CLI framework with the analysis name.
        """

    @classmethod
    @abc.abstractmethod
    def from_args(
        cls,
        args: argparse.Namespace,
    ) -> AbstractAnalysis[T]:
        """Create an instance configured from parsed CLI arguments."""
        ...

    @abc.abstractmethod
    def run(self, slither: SlitherCore) -> None:
        """Run the analysis over the project. Store results internally."""
        ...

    @abc.abstractmethod
    def display(self) -> None:
        """Display results to console using Rich formatting."""
        ...

    @abc.abstractmethod
    def serialize(self) -> List[T]:
        """Serialize results as typed dicts for JSON output.

        Returns a list of serialized analysis results (one per analyzed
        function). The dicts must contain only JSON-serializable types.
        """
        ...
