from decimal import Decimal
from typing import Dict, Union, List, Optional
from loguru import logger

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class ConstraintManager:
    ARITHMETIC_OPERATORS: set[BinaryType] = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }

    # Comparison operators
    COMPARISON_OPERATORS: set[BinaryType] = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    # Logical operators
    LOGICAL_OPERATORS: set[BinaryType] = {
        BinaryType.ANDAND,
        BinaryType.OROR,
    }

    def __init__(self):
        self._pending_constraints: Dict[str, Union[Binary, Variable]] = {}
        self.variable_manager = VariableManager()

    def add_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Add a pending constraint for a variable"""
        self._pending_constraints[var_name] = constraint
        # logger.debug(f"Added constraint for variable '{var_name}': {constraint}")

    def remove_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Remove and return a constraint for a variable"""
        constraint = self._pending_constraints.pop(var_name, None)
        # if constraint:
        #     logger.debug(f"Removed constraint for variable '{var_name}': {constraint}")
        return constraint

    def get_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Get constraint for a variable without removing it"""
        return self._pending_constraints.get(var_name)

    def has_constraint(self, var_name: str) -> bool:
        """Check if variable has a pending constraint"""
        return var_name in self._pending_constraints

    def get_all_constraints(self) -> Dict[str, Union[Binary, Variable]]:
        """Get all pending constraints"""
        return self._pending_constraints.copy()

    def clear_constraints(self, var_name: str = "") -> None:
        """Clear constraints for a specific variable or all constraints"""
        if var_name:
            if var_name in self._pending_constraints:
                del self._pending_constraints[var_name]
                logger.debug(f"Cleared constraint for variable '{var_name}'")
        else:
            self._pending_constraints.clear()
            logger.debug("Cleared all pending constraints")

    def get_constraint_count(self) -> int:
        """Get the number of pending constraints"""
        return len(self._pending_constraints)

    def list_constrained_variables(self) -> List[str]:
        """Get list of all variables with pending constraints"""
        return list(self._pending_constraints.keys())

    def enforce_constraints_on_variable(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Get and optionally remove constraint when enforcing (for one-time use constraints)"""
        return self.get_constraint(var_name)

    def peek_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Alias for get_constraint - clearer intent when just checking"""
        return self.get_constraint(var_name)

    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition"""

        variable_name = self.variable_manager.get_variable_name(condition_variable)
        constraint = self.get_constraint(variable_name)

        if isinstance(constraint, Binary):
            self.apply_constraint_from_binary_condition(constraint, domain)
        elif isinstance(constraint, Variable):
            self.apply_constraint_from_variable(constraint, domain)

    def apply_constraint_from_binary_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:

        if condition.type in self.COMPARISON_OPERATORS:
            self.apply_constraint_from_comparison_condition(condition, domain)

        pass

    def apply_constraint_from_comparison_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from comparison condition by refining variable bounds"""

        # Get the left and right operands
        left_operand = condition.variable_left
        right_operand = condition.variable_right

        left_is_variable = not self.is_operand_constant(left_operand, domain)
        right_is_variable = not self.is_operand_constant(right_operand, domain)

        if left_is_variable and not right_is_variable:

            # Case 1: variable < constant, variable > constant, etc.
            if not isinstance(left_operand, Variable):
                logger.error(f"Left operand is not a variable: {left_operand}")
                raise ValueError(f"Left operand is not a variable: {left_operand}")

            if not isinstance(right_operand, Constant):
                logger.error(f"Right operand is not a constant: {right_operand}")
                raise ValueError(f"Right operand is not a constant: {right_operand}")

            right_operand_value = right_operand.value

            if not isinstance(right_operand_value, int):
                logger.error(f"Right operand value is not an integer: {right_operand_value}")
                raise ValueError(f"Right operand value is not an integer: {right_operand_value}")

            self.update_variable_bounds_from_condition(
                left_operand, Decimal(right_operand_value), condition.type, domain
            )

        elif right_is_variable and not left_is_variable:

            # Case 2: constant < variable, constant > variable, etc.
            if not isinstance(right_operand, Variable):
                logger.error(f"Right operand is not a variable: {right_operand}")
                raise ValueError(f"Right operand is not a variable: {right_operand}")

            if not isinstance(left_operand, Constant):
                logger.error(f"Left operand is not a constant: {left_operand}")
                raise ValueError(f"Left operand is not a constant: {left_operand}")

            left_operand_value = left_operand.value

            if not isinstance(left_operand_value, int):
                logger.error(f"Left operand value is not an integer: {left_operand_value}")
                raise ValueError(f"Left operand value is not an integer: {left_operand_value}")

            # For constant < variable, we need to flip the operator
            flipped_op_type = self._flip_comparison_operator(condition.type)
            self.update_variable_bounds_from_condition(
                right_operand, Decimal(left_operand_value), flipped_op_type, domain
            )

        elif left_is_variable and right_is_variable:
            # Case 3: variable < variable, variable > variable, etc.
            if not isinstance(left_operand, Variable):
                logger.error(f"Left operand is not a variable: {left_operand}")
                raise ValueError(f"Left operand is not a variable: {left_operand}")

            if not isinstance(right_operand, Variable):
                logger.error(f"Right operand is not a variable: {right_operand}")
                raise ValueError(f"Right operand is not a variable: {right_operand}")

            self.update_variable_bounds_from_variable_comparison(
                left_operand, right_operand, condition.type, domain
            )

        else:
            # Case 4: constant < constant, constant > constant, etc.
            # This is a compile-time constant expression, no variables to constrain
            logger.debug(f"Constant comparison: {left_operand} {condition.type} {right_operand}")
            pass

    def update_variable_bounds_from_condition(
        self, variable: Variable, value: Decimal, op_type: BinaryType, domain: IntervalDomain
    ) -> None:
        """Update variable bounds from a condition"""
        # Get variable name and retrieve current state
        variable_name = self.variable_manager.get_variable_name(variable)

        # Handle case where variable doesn't exist in domain
        if variable_name not in domain.state.info:
            logger.error(f"Variable '{variable_name}' not found in domain state")
            raise ValueError(f"Variable '{variable_name}' not found in domain state")

        state_info = domain.state.info[variable_name]

        if op_type == BinaryType.EQUAL:
            # Nuke the intervals and set the exact value as valid
            state_info.interval_ranges = []  # Nuke intervals
            state_info.valid_values.add(value)  # Add the exact value
            return

        # Get type bounds for the variable
        type_min, type_max = state_info.get_type_bounds()

        # Create constraint range based on comparison operator
        constraint_range = self._create_constraint_range(value, op_type, type_min, type_max)

        # Apply constraint to all existing intervals
        constrained_ranges = []
        for existing_range in state_info.interval_ranges:
            intersection = existing_range.intersection(constraint_range)
            if intersection is not None:
                constrained_ranges.append(intersection)

        # Update the variable's interval ranges
        state_info.interval_ranges = constrained_ranges

        # Handle NOT_EQUAL operator by adding value to invalid_values
        if op_type == BinaryType.NOT_EQUAL:
            state_info.invalid_values.add(value)
            logger.debug(f"Added {value} to invalid values for {variable_name}")

        # If no valid intervals remain, the constraint is impossible
        if not constrained_ranges:
            logger.warning(
                f"Constraint {variable_name} {op_type} {value} creates impossible condition"
            )

    def _flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip a comparison operator for the reverse comparison"""
        if op_type == BinaryType.LESS:
            return BinaryType.GREATER
        elif op_type == BinaryType.LESS_EQUAL:
            return BinaryType.GREATER_EQUAL
        elif op_type == BinaryType.GREATER:
            return BinaryType.LESS
        elif op_type == BinaryType.GREATER_EQUAL:
            return BinaryType.LESS_EQUAL
        elif op_type == BinaryType.EQUAL:
            return BinaryType.EQUAL
        elif op_type == BinaryType.NOT_EQUAL:
            return BinaryType.NOT_EQUAL
        else:
            logger.warning(f"Unknown comparison operator for flipping: {op_type}")
            return op_type

    def update_variable_bounds_from_variable_comparison(
        self, left_var: Variable, right_var: Variable, op_type: BinaryType, domain: IntervalDomain
    ) -> None:
        """Update bounds for both variables in a variable-variable comparison"""
        left_var_name = self.variable_manager.get_variable_name(left_var)
        right_var_name = self.variable_manager.get_variable_name(right_var)

        # Get current state info for both variables
        if left_var_name not in domain.state.info:
            logger.warning(f"Variable '{left_var_name}' not found in domain state")
            return
        if right_var_name not in domain.state.info:
            logger.warning(f"Variable '{right_var_name}' not found in domain state")
            return

        left_state = domain.state.info[left_var_name]
        right_state = domain.state.info[right_var_name]

        # Get type bounds
        left_type_min, left_type_max = left_state.get_type_bounds()
        right_type_min, right_type_max = right_state.get_type_bounds()

        # Apply constraints based on operator
        if op_type == BinaryType.LESS:
            # left <= right - 1, right >= left + 1
            left_constraint = self._create_constraint_range(
                right_type_max - Decimal("1"), BinaryType.LESS_EQUAL, left_type_min, left_type_max
            )
            right_constraint = self._create_constraint_range(
                left_type_min + Decimal("1"),
                BinaryType.GREATER_EQUAL,
                right_type_min,
                right_type_max,
            )

        elif op_type == BinaryType.LESS_EQUAL:
            # left <= right, right >= left
            left_constraint = self._create_constraint_range(
                right_type_max, BinaryType.LESS_EQUAL, left_type_min, left_type_max
            )
            right_constraint = self._create_constraint_range(
                left_type_min, BinaryType.GREATER_EQUAL, right_type_min, right_type_max
            )

        elif op_type == BinaryType.GREATER:
            # left >= right + 1, right <= left - 1
            left_constraint = self._create_constraint_range(
                right_type_min + Decimal("1"),
                BinaryType.GREATER_EQUAL,
                left_type_min,
                left_type_max,
            )
            right_constraint = self._create_constraint_range(
                left_type_max - Decimal("1"), BinaryType.LESS_EQUAL, right_type_min, right_type_max
            )

        elif op_type == BinaryType.GREATER_EQUAL:
            # left >= right, right <= left
            left_constraint = self._create_constraint_range(
                right_type_min, BinaryType.GREATER_EQUAL, left_type_min, left_type_max
            )
            right_constraint = self._create_constraint_range(
                left_type_max, BinaryType.LESS_EQUAL, right_type_min, right_type_max
            )

        elif op_type == BinaryType.EQUAL:
            # left == right
            # Both variables must have the same value
            # Nuke the intervals and set valid values based on intersection
            left_valid_values = left_state.valid_values.deep_copy()
            right_valid_values = right_state.valid_values.deep_copy()

            # Get intersection of valid values from both variables
            intersection_values = left_valid_values.intersection(right_valid_values)

            # If both have valid values, use their intersection
            if not left_valid_values.is_empty() and not right_valid_values.is_empty():
                # Both variables have specific valid values - use intersection
                left_state.interval_ranges = []  # Nuke intervals
                right_state.interval_ranges = []  # Nuke intervals
                left_state.valid_values = intersection_values
                right_state.valid_values = intersection_values.deep_copy()
            else:

                left_constraint = IntervalRange(
                    lower_bound=left_type_min, upper_bound=left_type_max
                )
                right_constraint = IntervalRange(
                    lower_bound=right_type_min, upper_bound=right_type_max
                )

                # Apply constraints to both variables
                self._apply_constraint_to_variable(left_var_name, left_constraint, domain)
                self._apply_constraint_to_variable(right_var_name, right_constraint, domain)

            logger.debug(f"Applied equality constraint: {left_var_name} == {right_var_name}")
            return  # Early return since we handled this case specially

        elif op_type == BinaryType.NOT_EQUAL:
            # left != right

            left_constraint = IntervalRange(lower_bound=left_type_min, upper_bound=left_type_max)
            right_constraint = IntervalRange(lower_bound=right_type_min, upper_bound=right_type_max)

        else:
            logger.warning(f"Unknown comparison operator for variable comparison: {op_type}")
            return

        # Apply constraints to both variables
        self._apply_constraint_to_variable(left_var_name, left_constraint, domain)
        self._apply_constraint_to_variable(right_var_name, right_constraint, domain)

        logger.debug(
            f"Applied variable comparison constraint: {left_var_name} {op_type} {right_var_name}"
        )

    def _apply_constraint_to_variable(
        self, var_name: str, constraint_range: IntervalRange, domain: IntervalDomain
    ) -> None:
        """Apply a constraint range to a variable's existing intervals"""
        if var_name not in domain.state.info:
            return

        state_info = domain.state.info[var_name]

        # Apply constraint to all existing intervals
        constrained_ranges = []
        for existing_range in state_info.interval_ranges:
            intersection = existing_range.intersection(constraint_range)
            if intersection is not None:
                constrained_ranges.append(intersection)

        # Update the variable's interval ranges
        state_info.interval_ranges = constrained_ranges

    def _create_constraint_range(
        self, value: Decimal, op_type: BinaryType, type_min: Decimal, type_max: Decimal
    ) -> IntervalRange:
        """Create an interval range representing the constraint"""

        if op_type == BinaryType.LESS:
            # x < value -> [-inf, value-1]
            return IntervalRange(lower_bound=type_min, upper_bound=value - Decimal("1"))
        elif op_type == BinaryType.LESS_EQUAL:
            # x <= value -> [-inf, value]
            return IntervalRange(lower_bound=type_min, upper_bound=value)
        elif op_type == BinaryType.GREATER:
            # x > value -> [value+1, inf]
            return IntervalRange(lower_bound=value + Decimal("1"), upper_bound=type_max)
        elif op_type == BinaryType.GREATER_EQUAL:
            # x >= value -> [value, inf]
            return IntervalRange(lower_bound=value, upper_bound=type_max)
        elif op_type == BinaryType.EQUAL:
            # x == value -> [value, value]
            return IntervalRange(lower_bound=value, upper_bound=value)
        elif op_type == BinaryType.NOT_EQUAL:
            # x != value -> use full range, but add value to invalid_values
            # The actual invalidation will be handled in update_variable_bounds_from_condition
            return IntervalRange(lower_bound=type_min, upper_bound=type_max)
        else:
            # Unknown operator, return full range
            logger.warning(f"Unknown comparison operator: {op_type}")
            return IntervalRange(lower_bound=type_min, upper_bound=type_max)

    def is_operand_constant(
        self, operand: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain
    ) -> bool:
        """Check if an operand is a constant"""
        if isinstance(operand, Constant):
            return True
        if isinstance(operand, Variable):
            var_name = self.variable_manager.get_variable_name(operand)
            var_info = domain.state.info[var_name]
            if var_info.get_valid_values() == 1:
                return True
        return False
