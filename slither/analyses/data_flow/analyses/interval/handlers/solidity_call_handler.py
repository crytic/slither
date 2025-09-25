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
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall


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
            logger.debug(
                f"Require/assert function encountered: {operation.function.name} with condition: {condition_variable}"
            )
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
        
        if "byte" in operation.function.name:
            self._handle_byte(node, domain, operation)
            return

        # For other Solidity functions, log and continue without error
        logger.debug(f"Unhandled Solidity function: {operation.function.name} - skipping")
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
        logger.debug(f"Handled calldataload operation, created variable: {result_var_name}")

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
        logger.debug(f"Handled mload operation, created variable: {result_var_name}")

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
        
        logger.debug(f"Handled byte operation: byte({byte_index_arg}, {source_value_arg}) -> {result_var_name} (uint8)")

    def _handle_revert(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle revert operation by marking the branch as unreachable."""
        # Mark the domain as unreachable (TOP) to indicate this branch should not continue
        # to the final analysis
        domain.variant = DomainVariant.TOP
