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
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.sstore import (
    SstoreHandler,
    SSTORE_FUNCTIONS,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.sload import (
    SloadHandler,
    SLOAD_FUNCTIONS,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.mstore import (
    MstoreHandler,
    MSTORE_FUNCTIONS,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.mload import (
    MloadHandler,
    MLOAD_FUNCTIONS,
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
        self._sstore = SstoreHandler(solver)
        self._sload = SloadHandler(solver)
        self._mstore = MstoreHandler(solver)
        self._mload = MloadHandler(solver)

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

        if function_name in SSTORE_FUNCTIONS:
            self._sstore.handle(operation, domain, node)
            return

        if function_name in SLOAD_FUNCTIONS:
            self._sload.handle(operation, domain, node)
            return

        if function_name in MSTORE_FUNCTIONS:
            self._mstore.handle(operation, domain, node)
            return

        if function_name in MLOAD_FUNCTIONS:
            self._mload.handle(operation, domain, node)
            return

        logger.error_and_raise(
            f"Solidity function '{function_name}' is not implemented",
            NotImplementedError,
        )


__all__ = [
    "SolidityCallHandler",
    "RequireAssertHandler",
    "SstoreHandler",
    "SloadHandler",
    "MstoreHandler",
    "MloadHandler",
]
