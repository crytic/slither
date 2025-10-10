from typing import List

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
    IntervalRange,
)
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
    RangeVariable,
)
from slither.analyses.data_flow.analyses.interval.core.types.value_set import (
    ValueSet,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall
from IPython import embed

class SolidityCallHandler:
    """Handler for Solidity call operations, specifically require/assert functions."""

    def __init__(self, constraint_storage: ConstraintManager = None):
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ConstraintManager()

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle Solidity call operations including require/assert and calldataload"""

        logger.info(f"Handling solidity call: {operation.function.full_name}")
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        # Handle require/assert functions
        if operation.function.name in require_assert_functions:
            if not operation.arguments:
                logger.error("Operation arguments are empty")
                raise ValueError("Operation arguments are empty")

            condition_variable = operation.arguments[0]
            self.constraint_storage.apply_constraint_from_variable(condition_variable, domain)
            # logger.debug(
            #     f"Require/assert function encountered: {operation.function.name} with condition: {condition_variable}"
            # )
            return

        # Handle calldataload function
        if "calldata" in operation.function.name:
            self._handle_calldataload(node, domain, operation)
            return

        # Handle mload function
        if "mload" in operation.function.name:
            self._handle_mload(node, domain, operation)
            return

        # Handle revert function - mark branch as unreachable
        if "revert" in operation.function.name:
            self._handle_revert(node, domain, operation)
            return


        # Handle keccak256 hashing
        if operation.function.name.startswith("keccak256"):
            self._handle_keccak256(node, domain, operation)
            return

        # Handle abi.encode / abi.encodePacked family -> returns bytes
        if "encodePacked" in operation.function.name or "abi.encode" in operation.function.name:
            self._handle_abi_encode(node, domain, operation)
            return

        # Handle CREATE2 opcode exposed via solidity call wrappers
        if "create2" in operation.function.name or (
            hasattr(operation.function, "full_name") and "create2(" in operation.function.full_name
        ):
            self._handle_create2(node, domain, operation)
            return

        if "byte" in operation.function.name:
            self._handle_byte(node, domain, operation)
            return

        # General handling for solidity's type(...) expressions.
        # Model any type(...) derived value as opaque bytes, since its content is not used numerically.
        if "type(" in operation.function.name:
            self._handle_type_code(node, domain, operation)
            return

        if "balance(address)" == operation.function.full_name:
            self._handle_balance(node, domain, operation)
            return

        # For other Solidity functions, log and continue without error
        # logger.debug(f"Unhandled Solidity function: {operation.function.name} - skipping")
        return

    def _handle_calldataload(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle calldataload operation by creating a variable with unknown range."""
        # calldataload returns 32 bytes of data from calldata, treat as uint256
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        if not operation.lvalue:
            logger.error("calldataload operation has no lvalue")
            raise ValueError("calldataload operation has no lvalue")

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled calldataload operation, created variable: {result_var_name}")

    def _handle_mload(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mload operation by creating a variable with appropriate range."""
        # mload returns 32 bytes of data from memory, treat as uint256
        result_type = ElementaryType("uint256")

        # For now, treat mload as having full uint256 range
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        if not operation.lvalue:
            logger.error("mload operation has no lvalue")
            raise ValueError("mload operation has no lvalue")

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled mload operation, created variable: {result_var_name}")

    def _handle_byte(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle byte(n, x) operation - extracts the nth byte from x."""
        # byte(n, x) returns the nth byte of x, where the most significant byte is the 0th byte
        # The result is always a uint8 (0-255)
        
        if not operation.arguments or len(operation.arguments) != 2:
            logger.error(f"byte operation requires exactly 2 arguments, got {len(operation.arguments) if operation.arguments else 0}")
            raise ValueError(f"byte operation requires exactly 2 arguments")
        
        if not operation.lvalue:
            logger.error("byte operation has no lvalue")
            raise ValueError("byte operation has no lvalue")
        
        # Get the arguments: n (byte index) and x (source value)
        byte_index_arg = operation.arguments[0]
        source_value_arg = operation.arguments[1]
        
        # Get the range information for the source value
        source_range = RangeVariable.get_variable_info(domain, source_value_arg)
        
        # The result is always a uint8 (0-255)
        result_type = ElementaryType("uint8")
        result_range = IntervalRange(
            lower_bound=result_type.min,  # 0
            upper_bound=result_type.max,  # 255
        )
        
        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )
        
        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        
        # logger.debug(f"Handled byte operation: byte({byte_index_arg}, {source_value_arg}) -> {result_var_name} (uint8)")

    def _handle_revert(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle revert operation by marking the branch as unreachable."""
        # Mark the domain as unreachable (TOP) to indicate this branch should not continue
        # to the final analysis
        domain.variant = DomainVariant.TOP

    def _handle_keccak256(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle keccak256(...) returning bytes32."""
        if not operation.lvalue:
            logger.error("keccak256 operation has no lvalue")
            raise ValueError("keccak256 operation has no lvalue")

        result_type = ElementaryType("bytes32")
        # Hash output is opaque; we model as unconstrained bytes32 (no numeric intervals)
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled keccak256 call, created variable: {result_var_name} (bytes32)")

    def _handle_abi_encode(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle abi.encode / abi.encodePacked returning bytes memory."""
        if not operation.lvalue:
            logger.error("abi.encode operation has no lvalue")
            raise ValueError("abi.encode operation has no lvalue")

        result_type = ElementaryType("bytes")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
#        logger.debug(f"Handled {operation.function.name} -> {result_var_name} (bytes)")

    def _handle_type_code(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle solidity type(...) expressions conservatively as bytes memory."""
        if not operation.lvalue:
            logger.error("type(...) operation has no lvalue")
            raise ValueError("type(...) operation has no lvalue")

        result_type = ElementaryType("bytes")
        # Treat as dynamic bytes with unknown contents/length
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
#        logger.debug(f"Handled {operation.function.name} -> {result_var_name} (bytes)")

    def _handle_create2(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle create2(v, p, n, s) returning the new contract address or 0 on error.
        """
        if not operation.lvalue:
            logger.error("create2 operation has no lvalue")
            raise ValueError("create2 operation has no lvalue")

        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
#        logger.debug(f"Handled create2 call -> {result_var_name} (address)")

    def _handle_balance(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle balance(address) operation returning uint256."""
        if not operation.lvalue:
            logger.error("balance(address) operation has no lvalue")
            raise ValueError("balance(address) operation has no lvalue")

        result_type = ElementaryType("uint256")
        
        # Get the full range for uint256 type
        variable_manager = VariableInfoManager()
        type_bounds = variable_manager.get_type_bounds(result_type)
        
        result_range_variable = RangeVariable(
            interval_ranges=[type_bounds], 
            valid_values=ValueSet(set()), 
            invalid_values=ValueSet(set()), 
            var_type=result_type,
        )

        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled balance(address) call -> {result_var_name} (uint256)")