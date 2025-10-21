from decimal import Decimal

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.unary import Unary, UnaryType, logger

from IPython import embed


class UnaryHandler:
    def __init__(
        self, constraint_storage: ConstraintManager = None
    ):  # pyright: ignore[reportUndefinedVariable]
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ConstraintManager()
        self.variable_info_manager = VariableInfoManager()

    def handle_unary(self, node: Node, domain: IntervalDomain, operation: Unary):
        logger.info(f"Handling unary operation: {operation}")

        if operation.lvalue is None:
            logger.error("Unary operation lvalue is None")
            raise ValueError("Unary operation lvalue is None")

        temp_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        result_var_type = self.variable_info_manager.get_variable_type(operation.lvalue)

        if operation.type == UnaryType.BANG:
            # Logical NOT operation (!)
            self._handle_logical_not(domain, temp_var_name, operation)
        elif operation.type == UnaryType.TILD:
            # Bitwise NOT operation (~)
            self._handle_bitwise_not(domain, temp_var_name, operation, result_var_type)
        else:
            logger.error(f"Unsupported unary operation: {operation.type}")
            raise ValueError(f"Unsupported unary operation: {operation.type}")

    def _handle_logical_not(self, domain: IntervalDomain, temp_var_name: str, operation: Unary):
        """Handle logical NOT operation (!)."""
        # Store the unary operation constraint for future use
        logger.debug(f"Storing logical NOT operation constraint for variable {operation.lvalue}")
        self.constraint_storage.store_comparison_operation_constraint(operation, domain)

        # Create a range variable for the logical NOT result (boolean)
        range_variable = RangeVariable(
            interval_ranges=None,
            valid_values=ValueSet({0, 1}),  # Boolean can be 0 or 1
            invalid_values=ValueSet(set()),
            var_type=ElementaryType("bool"),
        )
        domain.state.set_range_variable(temp_var_name, range_variable)
        logger.debug(f"Created logical NOT result variable: {temp_var_name}")

    def _handle_bitwise_not(
        self,
        domain: IntervalDomain,
        temp_var_name: str,
        operation: Unary,
        result_var_type: ElementaryType,
    ):
        """Handle bitwise NOT operation (~)."""
        logger.debug(f"Handling bitwise NOT operation for variable {temp_var_name}")

        # Get the operand variable
        operand_var = operation.rvalue
        operand_name = self.variable_info_manager.get_variable_name(operand_var)

        # Check if the operand exists in the domain state
        if not domain.state.has_range_variable(operand_name):
            logger.warning(
                f"Operand {operand_name} not found in domain state, creating placeholder"
            )
            # Create a placeholder range variable for the result
            range_variable = RangeVariable(
                interval_ranges=[],  # Will be set to type bounds
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_var_type,
            )
            domain.state.set_range_variable(temp_var_name, range_variable)
            return

        # Get the operand's range variable
        operand_range_var = domain.state.get_range_variable(operand_name)

        # Compute bitwise NOT result
        result_range_var = self._compute_bitwise_not(operand_range_var, result_var_type)

        # Store the result
        domain.state.set_range_variable(temp_var_name, result_range_var)
        logger.debug(f"Computed bitwise NOT result: {result_range_var}")

    def _compute_bitwise_not(
        self, operand_range_var: RangeVariable, result_var_type: ElementaryType
    ) -> RangeVariable:
        """Compute the bitwise NOT of a range variable."""
        from decimal import Decimal

        # Get the type bounds for the result type
        type_min = Decimal(str(result_var_type.min))
        type_max = Decimal(str(result_var_type.max))

        # For bitwise NOT, we need to handle both valid values and interval ranges
        result_valid_values = ValueSet(set())
        result_interval_ranges = []

        # Handle valid values (discrete values)
        if not operand_range_var.valid_values.is_empty():
            for value in operand_range_var.valid_values:
                # Compute bitwise NOT: ~value
                bitwise_not_value = self._bitwise_not_value(value, result_var_type)
                result_valid_values.add(bitwise_not_value)

        # Handle interval ranges
        if operand_range_var.interval_ranges:
            for interval in operand_range_var.interval_ranges:
                # For interval ranges, we need to be more conservative
                # Bitwise NOT of [a, b] is approximately [~b, ~a] but we need to be careful about bounds
                lower_bound = self._bitwise_not_value(interval.upper_bound, result_var_type)
                upper_bound = self._bitwise_not_value(interval.lower_bound, result_var_type)

                # Ensure bounds are within type limits
                lower_bound = max(lower_bound, type_min)
                upper_bound = min(upper_bound, type_max)

                if lower_bound <= upper_bound:
                    from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                        IntervalRange,
                    )

                    result_interval_ranges.append(IntervalRange(lower_bound, upper_bound))

        # If we have no specific constraints, use the full type range
        if result_valid_values.is_empty() and not result_interval_ranges:
            from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                IntervalRange,
            )

            result_interval_ranges.append(IntervalRange(type_min, type_max))

        return RangeVariable(
            interval_ranges=result_interval_ranges,
            valid_values=result_valid_values,
            invalid_values=ValueSet(set()),
            var_type=result_var_type,
        )

    def _bitwise_not_value(self, value: Decimal, var_type: ElementaryType) -> Decimal:
        """Compute bitwise NOT of a single value."""

        # Convert to integer, perform bitwise NOT, then convert back
        int_value = int(value)

        # Get the bit width of the type
        if var_type.name.startswith("uint"):
            bit_width = int(var_type.name[4:])  # Extract number from 'uint256'
        elif var_type.name.startswith("int"):
            bit_width = int(var_type.name[3:])  # Extract number from 'int256'
        else:
            # Default to 256 bits for unknown types
            bit_width = 256

        # Create mask for the bit width
        mask = (1 << bit_width) - 1

        # Perform bitwise NOT and mask to the correct bit width
        result = (~int_value) & mask

        return Decimal(str(result))
