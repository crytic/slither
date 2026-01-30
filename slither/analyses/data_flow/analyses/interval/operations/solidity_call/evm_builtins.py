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

        self.logger.debug("Handling EVM builtin: {operation}", operation=operation)

        if not self._validate_preconditions(domain):
            return

        lvalue_name, return_type = self._resolve_lvalue_info(operation)
        if lvalue_name is None or return_type is None:
            return

        self._get_or_create_tracked(domain, lvalue_name, return_type)
        self.logger.debug(
            "Created unconstrained return variable for EVM builtin: {lvalue}",
            lvalue=lvalue_name,
        )

    def _validate_preconditions(self, domain: IntervalDomain) -> bool:
        """Validate solver and domain state."""
        if self.solver is None:
            self.logger.warning("Solver is None, skipping EVM builtin")
            return False
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping EVM builtin")
            return False
        return True

    def _resolve_lvalue_info(
        self, operation: SolidityCall
    ) -> tuple[Optional[str], Optional[ElementaryType]]:
        """Resolve lvalue name and return type from operation."""
        lvalue = operation.lvalue
        if lvalue is None:
            self.logger.debug("EVM builtin has no lvalue, nothing to track")
            return None, None

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            self.logger.debug("Could not resolve lvalue name for EVM builtin")
            return None, None

        return_type = self._resolve_return_type(lvalue)
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            self.logger.debug("Unsupported return type for EVM builtin: {type}", type=return_type)
            return None, None

        return lvalue_name, return_type

    def _resolve_return_type(self, lvalue) -> ElementaryType:
        """Resolve return type from lvalue, defaulting to uint256."""
        if hasattr(lvalue, "type"):
            resolved = IntervalSMTUtils.resolve_elementary_type(lvalue.type)
            if resolved is not None:
                return resolved
        return ElementaryType("uint256")

    def _get_or_create_tracked(
        self, domain: IntervalDomain, lvalue_name: str, return_type: ElementaryType
    ) -> None:
        """Get existing or create new tracked variable."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is None:
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked)
            tracked.assert_no_overflow(self.solver)
