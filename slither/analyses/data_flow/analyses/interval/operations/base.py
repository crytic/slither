"""Base class for operation handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from slither.slithir.operations import Operation
from slither.core.cfg.node import Node

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class BaseOperationHandler(ABC):
    """Abstract base class for operation handlers."""

    def __init__(self, solver: "SMTSolver"):
        self._solver = solver

    @property
    def solver(self) -> "SMTSolver":
        return self._solver

    @abstractmethod
    def handle(
        self,
        operation: Operation,
        domain: "IntervalDomain",
        node: Node,
    ) -> None:
        """Process operation, modifying domain in-place."""
