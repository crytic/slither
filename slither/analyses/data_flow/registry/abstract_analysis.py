"""Base class for configurable data-flow analyses."""

from __future__ import annotations

import abc
import argparse
from typing import ClassVar, Generic, List, TypeVar

from slither.core.slither_core import SlitherCore

T = TypeVar("T")
S = TypeVar("S")


class AbstractAnalysis(abc.ABC, Generic[T, S]):
    """Data-flow analysis with CLI flags, display, and serialization.

    Type parameters:
        T: Full serialized result type (CLI ``--json``).
        S: Lightweight summary type (MCP ProjectFacts).
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
    ) -> AbstractAnalysis[T, S]:
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
    def serialize(self) -> List[T]:
        """Full results for CLI ``--json`` output."""
        ...

    @abc.abstractmethod
    def summarize(self) -> List[S]:
        """Lightweight summaries for MCP ProjectFacts."""
        ...
