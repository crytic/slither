"""Base operation handler for interval analysis."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.logger import get_logger

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.core.cfg.node import Node
    from slither.slithir.operations.operation import Operation


class BaseOperationHandler(ABC):
    """Base class for operation handlers in interval analysis."""

    def __init__(
        self,
        solver: Optional["SMTSolver"] = None,
        analysis: Optional["IntervalAnalysis"] = None,
    ) -> None:
        """
        Initialize the operation handler.

        Args:
            solver: The SMT solver instance (optional)
            analysis: The interval analysis instance (optional, needed for interprocedural analysis)
        """
        self._solver = solver
        self._analysis = analysis
        self._logger = get_logger()

    @abstractmethod
    def handle(
        self,
        operation: Optional["Operation"],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """
        Handle an operation for interval analysis.

        Args:
            operation: The operation to handle (may be None for variable declarations)
            domain: The current interval domain
            node: The CFG node containing the operation
        """
        pass

    @property
    def solver(self) -> Optional["SMTSolver"]:
        """Get the SMT solver instance."""
        return self._solver

    @property
    def logger(self):
        """Get the logger instance."""
        return self._logger

    @property
    def analysis(self) -> Optional["IntervalAnalysis"]:
        """Get the interval analysis instance."""
        return self._analysis
