"""Binary operation handlers for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.binary import Binary

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.binary.arithmetic import (
    ArithmeticHandler,
    ARITHMETIC_OPERATIONS,
)
from slither.analyses.data_flow.analyses.interval.operations.binary.comparison import (
    ComparisonHandler,
    COMPARISON_OPERATIONS,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class BinaryHandler(BaseOperationHandler):
    """Dispatcher for binary operations.

    Routes arithmetic operations to ArithmeticHandler and
    comparison operations to ComparisonHandler.
    """

    def __init__(self, solver: "SMTSolver") -> None:
        super().__init__(solver)
        self._arithmetic = ArithmeticHandler(solver)
        self._comparison = ComparisonHandler(solver)

    def handle(
        self,
        operation: Binary,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Dispatch to appropriate handler based on operation type."""
        op_type = operation.type

        if op_type in ARITHMETIC_OPERATIONS:
            self._arithmetic.handle(operation, domain, node)
        elif op_type in COMPARISON_OPERATIONS:
            self._comparison.handle(operation, domain, node)


__all__ = ["BinaryHandler", "ArithmeticHandler", "ComparisonHandler"]
