"""Base class for rounding operation handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from slither.core.cfg.node import Node
from slither.slithir.operations import Operation

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )


class BaseOperationHandler(ABC):
    """Abstract base class for rounding operation handlers."""

    def __init__(self, analysis: "RoundingAnalysis"):
        self._analysis = analysis

    @property
    def analysis(self) -> "RoundingAnalysis":
        """Return the analysis instance."""
        return self._analysis

    @abstractmethod
    def handle(
        self,
        operation: Operation,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process operation, modifying domain in-place."""
