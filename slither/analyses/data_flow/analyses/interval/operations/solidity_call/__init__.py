"""Solidity call operation handler dispatch."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.solidity_call.asserts import (
    AssertHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.require import (
    RequireHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.revert import (
    RevertHandler,
)
from slither.slithir.operations.solidity_call import SolidityCall

from ..base import BaseOperationHandler

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class SolidityCallHandler(BaseOperationHandler):
    """Dispatch binary operations to specialised handlers."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if operation is None or not isinstance(operation, SolidityCall):
            self.logger.error_and_raise(
                "Invalid operation type: {operation_type}",
                ValueError,
                operation_type=type(operation).__name__,
            )
            return

        function_full_name = operation.function.full_name

        if "require" in function_full_name:
            RequireHandler(self.solver).handle(operation, domain, node)
        elif "assert" in function_full_name:
            AssertHandler(self.solver).handle(operation, domain, node)
        elif "revert" in function_full_name:
            RevertHandler(self.solver).handle(operation, domain, node)
        else:
            self.logger.error_and_raise(
                "Unknown function: {function_full_name}",
                ValueError,
                function_full_name=function_full_name,
            )
