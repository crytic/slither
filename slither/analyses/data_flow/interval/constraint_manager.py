from decimal import Decimal
from typing import Dict, Optional, Union

from slither.analyses.data_flow.interval.domain import IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.interval_calculator import IntervalCalculator
from slither.analyses.data_flow.interval.type_system import TypeSystem
from slither.analyses.data_flow.interval.variable_manager import VariableManager
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class ConstraintManager:
    """
    Handles constraint logic including pending constraints, require/assert handling,
    and constraint propagation between variables.
    """

    # Arithmetic operators
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

    def __init__(self, type_system: TypeSystem, variable_manager: VariableManager):
        self.type_system = type_system
        self.variable_manager = variable_manager
        self._pending_constraints: Dict[str, Union[Binary, Variable]] = {}

    def add_pending_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Add a pending constraint for a variable."""
        self._pending_constraints[var_name] = constraint

    def has_pending_constraint(self, var_name: str) -> bool:
        """Check if a variable has a pending constraint."""
        return var_name in self._pending_constraints

    def get_pending_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Get a pending constraint for a variable, if it exists."""
        return self._pending_constraints.get(var_name)

    def remove_pending_constraint(self, var_name: str) -> None:
        """Remove a pending constraint for a variable."""
        if var_name in self._pending_constraints:
            del self._pending_constraints[var_name]

    def clear_pending_constraints(self) -> None:
        """Clear all pending constraints."""
        self._pending_constraints.clear()

    def get_pending_constraints(self) -> Dict[str, Union[Binary, Variable]]:
        """Get all pending constraints."""
        return self._pending_constraints.copy()

    def apply_constraint_from_condition(
        self, condition: Union[Binary, Variable], domain: IntervalDomain
    ) -> None:
        """Extract and apply constraint from a condition in require/assert."""
        if isinstance(condition, Binary) and condition.type in self.COMPARISON_OPERATORS:
            # This is a comparison operation, apply the constraint
            self.apply_comparison_constraint_from_operation(condition, domain)
        elif isinstance(condition, Binary) and condition.type in self.LOGICAL_OPERATORS:
            # This is a logical operation, recursively extract constraints from operands
            self.apply_logical_constraint_from_operation(condition, domain)
        elif isinstance(condition, Variable):
            # The condition is a variable, check if we have a pending constraint for it
            self.apply_pending_constraint_for_variable(condition, domain)

    def apply_pending_constraint_for_variable(self, var: Variable, domain: IntervalDomain) -> None:
        """Apply pending constraint for a variable if it exists."""
        var_name: str = self.variable_manager.get_canonical_name(var)

        if not self.has_pending_constraint(var_name):
            return

        constraint_operation = self.get_pending_constraint(var_name)
        if constraint_operation is None:
            return

        # Apply the constraint based on its type
        if isinstance(constraint_operation, Binary):
            if constraint_operation.type in self.LOGICAL_OPERATORS:
                self.apply_logical_constraint_from_operation(constraint_operation, domain)
            elif constraint_operation.type in self.COMPARISON_OPERATORS:
                self.apply_comparison_constraint_from_operation(constraint_operation, domain)

        # Remove the constraint from pending since it's now applied
        self.remove_pending_constraint(var_name)

    def apply_comparison_constraint_from_operation(
        self, operation: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from a comparison operation."""
        if not hasattr(operation, "variable_left") or not hasattr(operation, "variable_right"):
            return

        left_var: Union[Variable, Constant, RVALUE, Function] = operation.variable_left
        right_var: Union[Variable, Constant, RVALUE, Function] = operation.variable_right
        left_interval: IntervalInfo = self._retrieve_interval_info(left_var, domain, operation)
        right_interval: IntervalInfo = self._retrieve_interval_info(right_var, domain, operation)

        # Determine variable types
        left_is_variable: bool = isinstance(left_var, Variable) and not isinstance(
            left_var, Constant
        )
        right_is_variable: bool = isinstance(right_var, Variable) and not isinstance(
            right_var, Constant
        )

        # Handle different comparison scenarios
        if left_is_variable and not right_is_variable:
            if isinstance(left_var, Variable):
                self.update_variable_bounds_from_comparison(
                    left_var, right_interval, operation.type, domain
                )
        elif not left_is_variable and right_is_variable:
            flipped_op: BinaryType = self.flip_comparison_operator(operation.type)
            if isinstance(right_var, Variable):
                self.update_variable_bounds_from_comparison(
                    right_var, left_interval, flipped_op, domain
                )
        elif left_is_variable and right_is_variable:
            if isinstance(left_var, Variable) and isinstance(right_var, Variable):
                self.handle_variable_to_variable_comparison(
                    left_var, right_var, operation.type, domain
                )

    def update_variable_bounds_from_comparison(
        self,
        variable: Variable,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Update variable bounds based on comparison operation."""
        var_name: str = self.variable_manager.get_canonical_name(variable)
        current_interval: IntervalInfo = self.variable_manager.create_interval_for_variable(
            variable, domain.state.info
        )
        constraint_value: Decimal = constraint_interval.lower_bound
        new_interval: IntervalInfo = current_interval.deep_copy()

        # Apply comparison constraints
        IntervalCalculator.apply_comparison_constraint_to_interval(
            new_interval, constraint_value, op_type
        )

        # Check for invalid interval
        if not IntervalCalculator.is_valid_interval(new_interval):
            domain.variant = domain.variant.BOTTOM
            raise ValueError(f"Invalid interval: {new_interval}")

        domain.state.info[var_name] = new_interval

    def handle_variable_to_variable_comparison(
        self,
        left_var: Variable,
        right_var: Variable,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Handle comparison between two variables."""
        left_name: str = self.variable_manager.get_canonical_name(left_var)
        right_name: str = self.variable_manager.get_canonical_name(right_var)

        left_interval: Optional[IntervalInfo] = domain.state.info.get(left_name)
        right_interval: Optional[IntervalInfo] = domain.state.info.get(right_name)

        if not left_interval or not right_interval:
            return

        new_left: IntervalInfo = left_interval.deep_copy()
        new_right: IntervalInfo = right_interval.deep_copy()

        # Apply variable-to-variable comparison constraints
        self._apply_variable_comparison_constraints(new_left, new_right, op_type)

        # Check for invalid intervals
        if not IntervalCalculator.is_valid_interval(
            new_left
        ) or not IntervalCalculator.is_valid_interval(new_right):
            domain.variant = domain.variant.BOTTOM
            return

        domain.state.info[left_name] = new_left
        domain.state.info[right_name] = new_right

    def _apply_variable_comparison_constraints(
        self, left: IntervalInfo, right: IntervalInfo, op_type: BinaryType
    ) -> None:
        """Apply constraints for variable-to-variable comparisons."""
        if op_type == BinaryType.EQUAL:
            IntervalCalculator.apply_equality_constraints(left, right)
        elif op_type == BinaryType.NOT_EQUAL:
            IntervalCalculator.apply_inequality_constraints(left, right)
        elif op_type == BinaryType.LESS:
            IntervalCalculator.apply_less_than_constraints(left, right)
        elif op_type == BinaryType.LESS_EQUAL:
            IntervalCalculator.apply_less_equal_constraints(left, right)
        elif op_type == BinaryType.GREATER:
            IntervalCalculator.apply_greater_than_constraints(left, right)
        elif op_type == BinaryType.GREATER_EQUAL:
            IntervalCalculator.apply_greater_equal_constraints(left, right)

    def apply_logical_constraint_from_operation(
        self, operation: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraints from a logical operation by recursively extracting constraints from operands."""
        if not hasattr(operation, "variable_left") or not hasattr(operation, "variable_right"):
            return

        left_operand: Union[Variable, Constant, RVALUE, Function] = operation.variable_left
        right_operand: Union[Variable, Constant, RVALUE, Function] = operation.variable_right

        # Recursively apply constraints
        self.apply_constraint_from_operand(left_operand, domain)
        self.apply_constraint_from_operand(right_operand, domain)

    def apply_constraint_from_operand(
        self, operand: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain
    ) -> None:
        """Apply constraint from a single operand of a logical operation."""
        if isinstance(operand, Binary) and operand.type in self.COMPARISON_OPERATORS:
            self.apply_comparison_constraint_from_operation(operand, domain)
        elif isinstance(operand, Binary) and operand.type in self.LOGICAL_OPERATORS:
            self.apply_logical_constraint_from_operation(operand, domain)
        elif isinstance(operand, Variable):
            # The operand is a variable, check if we have a pending constraint for it
            self.apply_pending_constraint_for_variable(operand, domain)
        else:
            raise ValueError(f"Unknown operand type: {operand}")

    def flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip comparison operator for handling constant-variable comparisons."""
        flip_map: Dict[BinaryType, BinaryType] = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,
        }
        return flip_map[op_type]

    def _retrieve_interval_info(
        self, var: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain, operation
    ) -> IntervalInfo:
        """Retrieve interval information for a variable or constant."""
        if isinstance(var, Constant):
            value: Decimal = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            var_name: str = self.variable_manager.get_canonical_name(var)
            return domain.state.info.get(var_name, IntervalInfo(var_type=None))
        return IntervalInfo(var_type=None)
