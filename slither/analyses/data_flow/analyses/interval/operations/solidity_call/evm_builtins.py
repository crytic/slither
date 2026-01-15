"""Handler for EVM environment builtins in interval analysis.

Handles opcodes that return environment/context information:
- returndatasize() - size of return data from last call
- calldatasize() - size of calldata
- codesize() - size of current contract's code
- extcodesize(address) - size of external contract's code
- selfbalance() - balance of current contract
- chainid() - current chain ID
- origin() - transaction origin address (as uint160)
- gasprice() - gas price of transaction
- coinbase() - current block's miner address (as uint160)
- difficulty() / prevrandao() - block difficulty/randomness
- number() - current block number
- basefee() - base fee
- caller() - msg.sender address (as uint160)
- callvalue() - msg.value
- address() - current contract address (as uint160)
- balance(address) - balance of an address
- extcodehash(address) - code hash of an address
- blockhash(uint256) - hash of a given block
- sload(uint256) - storage load
- keccak256(...) - hash function
- sha3(...) - alias for keccak256
- add/sub/mul/div/mod/exp - arithmetic in assembly
- and/or/xor/not - bitwise operations
- shl/shr/sar - shift operations
- iszero - zero check
- eq/lt/gt/slt/sgt - comparisons
- signextend - sign extension
- returndatacopy - copy return data to memory
- codecopy - copy code to memory
- extcodecopy - copy external code to memory
- create/create2 - contract creation
- selfdestruct - contract destruction
- log0/log1/log2/log3/log4 - logging
- invalid - invalid opcode
- stop - stop execution
- return - return from call
- revert - revert execution (already handled elsewhere)

All of these return uint256 (or address which is uint160) and are modeled
as unconstrained within their type bounds.
"""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class EvmBuiltinHandler(BaseOperationHandler):
    """Handle EVM environment/context builtins that return values.

    These opcodes return values that are unknown at compile time,
    so we model them as unconstrained within their type bounds.
    """

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: IntervalDomain,
        node: "Node",
    ) -> None:
        if operation is None:
            return

        self.logger.debug(
            "Handling EVM builtin: {operation}",
            operation=operation,
        )

        if self.solver is None:
            self.logger.warning("Solver is None, skipping EVM builtin")
            return

        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping EVM builtin")
            return

        # Get the lvalue (return value) of the call
        lvalue = operation.lvalue
        if lvalue is None:
            # Some builtins don't have return values (e.g., log0, stop, selfdestruct)
            self.logger.debug("EVM builtin has no lvalue, nothing to track")
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            self.logger.debug("Could not resolve lvalue name for EVM builtin")
            return

        # Resolve the return type from the lvalue, default to uint256
        return_type: Optional[ElementaryType] = None
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Most EVM builtins return uint256, fallback if we couldn't resolve
        if return_type is None:
            return_type = ElementaryType("uint256")

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            self.logger.debug(
                "Unsupported return type for EVM builtin: {type}",
                type=return_type,
            )
            return

        # Create a tracked variable for the return value with full range (unconstrained)
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_tracked is None:
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if lvalue_tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        self.logger.debug(
            "Created unconstrained return variable for EVM builtin: {lvalue}",
            lvalue=lvalue_name,
        )
