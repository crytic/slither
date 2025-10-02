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

    def _handle_and(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle and(x, y) operation - bitwise AND of x and y."""
        # and(x, y) returns the bitwise AND of x and y
        # The result has the same type as the operands
        
        if not operation.arguments or len(operation.arguments) != 2:
            logger.error(f"and operation requires exactly 2 arguments, got {len(operation.arguments) if operation.arguments else 0}")
            raise ValueError(f"and operation requires exactly 2 arguments")
        
        if not operation.lvalue:
            logger.error("and operation has no lvalue")
            raise ValueError("and operation has no lvalue")
        
        # Get the arguments: x and y
        x_arg = operation.arguments[0]
        y_arg = operation.arguments[1]
        
        # Get the range information for both operands
        x_range = RangeVariable.get_variable_info(domain, x_arg)
        y_range = RangeVariable.get_variable_info(domain, y_arg)
        
        # Compute the bitwise AND result
        result_range_variable = self._compute_bitwise_and(x_range, y_range)
        
        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        
        logger.debug(f"Handled and operation: and({x_arg}, {y_arg}) -> {result_var_name}")

    def _compute_bitwise_and(self, x_range: RangeVariable, y_range: RangeVariable) -> RangeVariable:
        """Compute the bitwise AND of two range variables."""
        # For bitwise AND, we need to consider the intersection of bits
        # The result can be at most the minimum of the two operands
        # and at least 0
        
        result_interval_ranges = []
        
        # Handle case where both operands have interval ranges
        if x_range.interval_ranges and y_range.interval_ranges:
            for x_interval in x_range.interval_ranges:
                for y_interval in y_range.interval_ranges:
                    # For bitwise AND: result <= min(x, y) and result >= 0
                    min_upper = min(x_interval.get_upper(), y_interval.get_upper())
                    result_interval = IntervalRange(0, min_upper)
                    result_interval_ranges.append(result_interval)
        
        # Handle case where one operand has valid values and the other has intervals
        if x_range.valid_values and not x_range.valid_values.is_empty() and y_range.interval_ranges:
            for x_val in x_range.valid_values:
                for y_interval in y_range.interval_ranges:
                    min_upper = min(x_val, y_interval.get_upper())
                    result_interval = IntervalRange(0, min_upper)
                    result_interval_ranges.append(result_interval)
        
        if y_range.valid_values and not y_range.valid_values.is_empty() and x_range.interval_ranges:
            for y_val in y_range.valid_values:
                for x_interval in x_range.interval_ranges:
                    min_upper = min(y_val, x_interval.get_upper())
                    result_interval = IntervalRange(0, min_upper)
                    result_interval_ranges.append(result_interval)
        
        # Handle case where both operands have valid values
        if (x_range.valid_values and not x_range.valid_values.is_empty() and 
            y_range.valid_values and not y_range.valid_values.is_empty()):
            result_valid_values = set()
            for x_val in x_range.valid_values:
                for y_val in y_range.valid_values:
                    # Convert to int for bitwise operation, then back to Decimal
                    from decimal import Decimal
                    result_val = int(x_val) & int(y_val)
                    result_valid_values.add(Decimal(result_val))
            
            # Create result with valid values
            from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
            result_valid_set = ValueSet(result_valid_values)
            
            return RangeVariable(
                interval_ranges=result_interval_ranges,
                valid_values=result_valid_set,
                invalid_values=None,
                var_type=x_range.var_type,  # Use the type of the first operand
            )
        
        # If no valid values, return with just interval ranges
        return RangeVariable(
            interval_ranges=result_interval_ranges,
            valid_values=None,
            invalid_values=None,
            var_type=x_range.var_type,  # Use the type of the first operand
        )

    def _handle_revert(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle revert operation by marking the branch as unreachable."""
        # Mark the domain as unreachable (TOP) to indicate this branch should not continue
        # to the final analysis
        domain.variant = DomainVariant.TOP
