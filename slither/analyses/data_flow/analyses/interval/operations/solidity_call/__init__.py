"""Solidity call operation handlers for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.solidity_call import SolidityCall

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.require_assert import (
    RequireAssertHandler,
    REQUIRE_ASSERT_FUNCTIONS,
)
from slither.analyses.data_flow.logger import get_logger

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

logger = get_logger()


class SolidityCallHandler(BaseOperationHandler):
    """Dispatcher for Solidity built-in function calls.

    Routes to specialized handlers based on function name.
    """

    def __init__(self, solver: "SMTSolver") -> None:
        super().__init__(solver)
        self._require_assert = RequireAssertHandler(solver)

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Dispatch to appropriate handler based on function name."""
        function_name = operation.function.full_name

        if function_name in REQUIRE_ASSERT_FUNCTIONS:
            self._require_assert.handle(operation, domain, node)
            return

        logger.error_and_raise(
            f"Solidity function '{function_name}' is not implemented",
            NotImplementedError,
        )


__all__ = ["SolidityCallHandler", "RequireAssertHandler"]
