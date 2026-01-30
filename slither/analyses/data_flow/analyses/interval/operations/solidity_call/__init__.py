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
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.calldata_load import (
    CalldataLoadHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.byte import (
    ByteHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.timestamp import (
    TimestampHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.gas import (
    GasHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.low_level_call import (
    LowLevelCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.evm_builtins import (
    EvmBuiltinHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.memory import (
    MemoryLoadHandler,
    MemoryStoreHandler,
    CalldataCopyHandler,
)
from slither.slithir.operations.solidity_call import SolidityCall

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler

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

        if self._try_dispatch_by_substring(function_full_name, operation, domain, node):
            return

        if self._try_dispatch_by_prefix(function_full_name, operation, domain, node):
            return

        self.logger.debug(
            "Using generic EVM builtin handler for: {function_full_name}",
            function_full_name=function_full_name,
        )
        EvmBuiltinHandler(self.solver).handle(operation, domain, node)

    def _try_dispatch_by_substring(
        self, name: str, operation: SolidityCall, domain: "IntervalDomain", node: "Node"
    ) -> bool:
        """Try to dispatch based on substring match. Returns True if handled."""
        substring_handlers = [
            ("require", lambda: RequireHandler(self.solver)),
            ("assert", lambda: AssertHandler(self.solver)),
            ("revert", lambda: RevertHandler(self.solver)),
            ("calldataload", lambda: CalldataLoadHandler(self.solver, self.analysis)),
            ("byte(", lambda: ByteHandler(self.solver)),
            ("timestamp()", lambda: TimestampHandler(self.solver)),
            ("calldatacopy", lambda: CalldataCopyHandler(self.solver)),
        ]

        for substring, handler_factory in substring_handlers:
            if substring in name:
                handler_factory().handle(operation, domain, node)
                return True

        if "gas()" in name or "gasleft()" in name:
            GasHandler(self.solver).handle(operation, domain, node)
            return True

        return False

    def _try_dispatch_by_prefix(
        self, name: str, operation: SolidityCall, domain: "IntervalDomain", node: "Node"
    ) -> bool:
        """Try to dispatch based on prefix match. Returns True if handled."""
        # Low-level call opcodes
        call_prefixes = ("call(", "staticcall(", "delegatecall(", "callcode(")
        if any(name.startswith(p) for p in call_prefixes):
            LowLevelCallHandler(self.solver).handle(operation, domain, node)
            return True

        # Memory operations
        if name.startswith("mstore8("):
            MemoryStoreHandler(self.solver, self.analysis, byte_size=1).handle(
                operation, domain, node
            )
            return True

        if name.startswith("mstore("):
            MemoryStoreHandler(self.solver, self.analysis, byte_size=32).handle(
                operation, domain, node
            )
            return True

        if name.startswith("mload("):
            MemoryLoadHandler(self.solver, self.analysis).handle(operation, domain, node)
            return True

        return False