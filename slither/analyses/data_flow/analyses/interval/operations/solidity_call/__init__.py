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

        # Dispatch require/assert/revert by substring as they are high-level helpers.
        if "require" in function_full_name:
            RequireHandler(self.solver).handle(operation, domain, node)
            return

        if "assert" in function_full_name:
            AssertHandler(self.solver).handle(operation, domain, node)
            return

        if "revert" in function_full_name:
            RevertHandler(self.solver).handle(operation, domain, node)
            return

        # Handle low-level builtin calldataload(uint256).
        if "calldataload" in function_full_name:
            CalldataLoadHandler(self.solver).handle(operation, domain, node)
            return

        # Handle low-level builtin byte(uint256,uint256).
        if "byte(" in function_full_name:
            ByteHandler(self.solver).handle(operation, domain, node)
            return

        # Handle timestamp() which returns block.timestamp.
        if "timestamp()" in function_full_name:
            TimestampHandler(self.solver).handle(operation, domain, node)
            return

        # Handle gas()/gasleft() which returns remaining gas.
        if "gas()" in function_full_name or "gasleft()" in function_full_name:
            GasHandler(self.solver).handle(operation, domain, node)
            return

        # Handle low-level EVM call opcodes (call, staticcall, delegatecall, callcode).
        # These return a boolean success value.
        if (
            function_full_name.startswith("call(")
            or function_full_name.startswith("staticcall(")
            or function_full_name.startswith("delegatecall(")
            or function_full_name.startswith("callcode(")
        ):
            LowLevelCallHandler(self.solver).handle(operation, domain, node)
            return

        # Handle low-level memory builtins (mstore/mstore8/mload).
        if (
            function_full_name.startswith("mstore(")
            or function_full_name.startswith("mstore8(")
            or function_full_name.startswith("mload(")
        ):
            # Branch: mstore8 uses a single byte, mstore uses a full word.
            if function_full_name.startswith("mstore8("):
                MemoryStoreHandler(self.solver, byte_size=1).handle(operation, domain, node)
                return

            if function_full_name.startswith("mstore("):
                MemoryStoreHandler(self.solver, byte_size=32).handle(operation, domain, node)
                return

            MemoryLoadHandler(self.solver).handle(operation, domain, node)
            return

        # Handle calldatacopy(uint256,uint256,uint256).
        # This operation copies calldata to memory but doesn't return a value, so we treat it as a no-op.
        if "calldatacopy" in function_full_name:
            CalldataCopyHandler(self.solver).handle(operation, domain, node)
            return

        # Fallback: handle any other EVM builtin generically.
        # This covers opcodes like returndatasize, calldatasize, codesize, chainid,
        # origin, gasprice, coinbase, difficulty, number, basefee, caller, callvalue,
        # address, balance, extcodehash, blockhash, sload, keccak256, arithmetic ops, etc.
        # These are modeled as returning unconstrained values within their type bounds.
        self.logger.debug(
            "Using generic EVM builtin handler for: {function_full_name}",
            function_full_name=function_full_name,
        )
        EvmBuiltinHandler(self.solver).handle(operation, domain, node)