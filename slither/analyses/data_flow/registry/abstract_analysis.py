"""Base class for configurable data-flow analyses."""

from __future__ import annotations

import abc
import argparse
from typing import ClassVar, Generic, TypeVar

from slither.core.slither_core import SlitherCore

ResultType = TypeVar("ResultType")
SummaryType = TypeVar("SummaryType")


class AbstractAnalysis(abc.ABC, Generic[ResultType, SummaryType]):
    """Data-flow analysis with CLI flags, display, and serialization.

    Type parameters:
        ResultType: Full serialized result type (CLI ``--json``).
        SummaryType: Lightweight summary type (MCP ProjectFacts).
    """

    ARGUMENT: ClassVar[str]
    HELP: ClassVar[str]

    @classmethod
    def register_arguments(
        cls,
        group: argparse._ArgumentGroup,
    ) -> None:
        """Register analysis-specific CLI flags."""

    @classmethod
    @abc.abstractmethod
    def from_args(
        cls,
        args: argparse.Namespace,
    ) -> AbstractAnalysis[ResultType, SummaryType]:
        """Create instance from parsed CLI arguments."""
        ...

    @abc.abstractmethod
    def run(self, slither: SlitherCore) -> None:
        """Run analysis and store results internally."""
        ...

    @abc.abstractmethod
    def display(self) -> None:
        """Display results with Rich formatting."""
        ...

    @abc.abstractmethod
    def serialize(self) -> list[ResultType]:
        """Full results for CLI ``--json`` output."""
        ...

    @abc.abstractmethod
    def summarize(self) -> list[SummaryType]:
        """Lightweight summaries for MCP ProjectFacts."""
        ...
