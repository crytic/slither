from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union
from loguru import logger

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
import math


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
        self._temp_var_mappings: Dict[str, Binary] = (
            {}
        )  # Track temp vars to their source expressions

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

    def add_temp_var_mapping(self, temp_var_name: str, source_expression: Binary) -> None:
        """Track a temporary variable's source arithmetic expression."""
        self._temp_var_mappings[temp_var_name] = source_expression

    def get_temp_var_mapping(self, temp_var_name: str) -> Optional[Binary]:
        """Get the source expression for a temporary variable."""
        return self._temp_var_mappings.get(temp_var_name)

    def has_temp_var_mapping(self, temp_var_name: str) -> bool:
        """Check if a temporary variable has a source expression mapping."""
        return temp_var_name in self._temp_var_mappings

    def apply_constraint_from_condition(
        self, condition: Union[Binary, Variable], domain: IntervalDomain
    ) -> None:
        """Extract and apply constraint from a condition in require/assert."""

        if isinstance(condition, Binary) and condition.type in self.COMPARISON_OPERATORS:
            self.apply_comparison_constraint_from_operation(condition, domain)
        elif isinstance(condition, Binary) and condition.type in self.LOGICAL_OPERATORS:
            self.apply_logical_constraint_from_operation(condition, domain)
        elif isinstance(condition, Variable):
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

        # Determine variable types using the new helper method
        left_is_variable: bool = isinstance(
            left_var, Variable
        ) and not self._is_effectively_constant(left_var, domain)
        right_is_variable: bool = isinstance(
            right_var, Variable
        ) and not self._is_effectively_constant(right_var, domain)

        # Handle different comparison scenarios
        if left_is_variable and not right_is_variable:
            if isinstance(left_var, Variable):
                # Check if this is a temporary variable with an arithmetic mapping
                left_var_name = self.variable_manager.get_canonical_name(left_var)

                if self.has_temp_var_mapping(left_var_name):
                    source_expr = self.get_temp_var_mapping(left_var_name)
                    if source_expr:
                        # Handle as arithmetic constraint
                        self.handle_arithmetic_comparison_constraint(
                            source_expr, right_interval, operation.type, domain, is_left=True
                        )
                else:
                    # Handle as regular variable constraint
                    self.update_variable_bounds_from_comparison(
                        left_var, right_interval, operation.type, domain
                    )
        elif not left_is_variable and right_is_variable:
            flipped_op: BinaryType = self.flip_comparison_operator(operation.type)
            if isinstance(right_var, Variable):
                # Check if this is a temporary variable with an arithmetic mapping
                right_var_name = self.variable_manager.get_canonical_name(right_var)
                if self.has_temp_var_mapping(right_var_name):
                    source_expr = self.get_temp_var_mapping(right_var_name)
                    if source_expr:
                        # Handle as arithmetic constraint
                        self.handle_arithmetic_comparison_constraint(
                            source_expr, left_interval, flipped_op, domain, is_left=False
                        )
                else:
                    # Handle as regular variable constraint
                    self.update_variable_bounds_from_comparison(
                        right_var, left_interval, flipped_op, domain
                    )
        elif left_is_variable and right_is_variable:
            if isinstance(left_var, Variable) and isinstance(right_var, Variable):
                self.handle_variable_to_variable_comparison(
                    left_var, right_var, operation.type, domain
                )
        else:
            pass

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
            logger.error(f"Invalid interval: {new_interval}")
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

    def _is_effectively_constant(
        self, var: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain
    ) -> bool:
        """Check if a variable is effectively a constant (either Constant type or variable with tight bounds)."""
        if isinstance(var, Constant):
            return True
        elif isinstance(var, Variable):
            # Check if this variable has tight bounds (effectively a constant)
            var_name = self.variable_manager.get_canonical_name(var)
            interval = domain.state.info.get(var_name)
            if interval and interval.lower_bound == interval.upper_bound:
                return True
        return False

    def handle_arithmetic_comparison_constraint(
        self,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
        is_left: bool,
    ) -> None:
        """Handle constraint propagation for arithmetic expressions in comparisons."""
        # Extract variables from the arithmetic expression
        variables_in_expr = self._extract_variables_from_arithmetic(arithmetic_expr, domain)

        if not variables_in_expr:
            return

        # For now, handle simple cases with one variable
        if len(variables_in_expr) == 1:
            var = variables_in_expr[0]

            self._propagate_arithmetic_constraint_to_variable(
                var, arithmetic_expr, constraint_interval, op_type, domain
            )
        else:
            logger.error(f"\tMultiple variables in expression. Implement affine relations.")

    def _extract_variables_from_arithmetic(
        self, arithmetic_expr: Binary, domain: Optional[IntervalDomain] = None
    ) -> List[Variable]:
        """Extract all variables from an arithmetic expression."""
        variables: List[Variable] = []

        def extract_from_operand(operand):
            if isinstance(operand, Variable):
                # Check if this variable is effectively a constant
                if domain and self._is_effectively_constant(operand, domain):
                    pass  # Skip constants
                else:
                    variables.append(operand)

        extract_from_operand(arithmetic_expr.variable_left)
        extract_from_operand(arithmetic_expr.variable_right)

        return variables

    def _propagate_arithmetic_constraint_to_variable(
        self,
        variable: Variable,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Propagate arithmetic constraint back to the original variable."""
        if arithmetic_expr.type == BinaryType.ADDITION:
            self._solve_addition_constraint(
                variable, arithmetic_expr, constraint_interval, op_type, domain
            )
        elif arithmetic_expr.type == BinaryType.SUBTRACTION:
            self._solve_subtraction_constraint(
                variable, arithmetic_expr, constraint_interval, op_type, domain
            )
        elif arithmetic_expr.type == BinaryType.DIVISION:
            self._solve_division_constraint(
                variable, arithmetic_expr, constraint_interval, op_type, domain
            )
        elif arithmetic_expr.type == BinaryType.MULTIPLICATION:
            self._solve_multiplication_constraint(
                variable, arithmetic_expr, constraint_interval, op_type, domain
            )

    def _solve_addition_constraint(
        self,
        variable: Variable,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x + constant > value for x."""
        constant_value = self._extract_constant_from_arithmetic(variable, arithmetic_expr, domain)
        if constant_value is None:
            return

        # Solve: x + constant > value => x > value - constant
        constraint_value = constraint_interval.lower_bound
        new_constraint_value = constraint_value - constant_value
        new_op_type = op_type  # Keep the same operator

        self._apply_constraint_to_variable(variable, new_constraint_value, new_op_type, domain)

    def _solve_subtraction_constraint(
        self,
        variable: Variable,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x - constant > value for x."""
        constant_value, is_variable_on_left = self._extract_constant_from_arithmetic_with_position(
            variable, arithmetic_expr, domain
        )
        if constant_value is None:
            return

        constraint_value = constraint_interval.lower_bound

        if is_variable_on_left:
            # x - constant > value => x > value + constant
            new_constraint_value = constraint_value + constant_value
            new_op_type = op_type  # Keep the same operator
        else:
            # constant - x > value => x < constant - value
            new_constraint_value = constant_value - constraint_value
            new_op_type = self.flip_comparison_operator(op_type)  # Flip the operator

        self._apply_constraint_to_variable(variable, new_constraint_value, new_op_type, domain)

    def _extract_constant_from_arithmetic(
        self, variable: Variable, arithmetic_expr: Binary, domain: Optional[IntervalDomain] = None
    ) -> Optional[Decimal]:
        """Extract constant value from arithmetic expression where variable is one operand."""
        if arithmetic_expr.variable_left == variable:
            constant_operand = arithmetic_expr.variable_right
        elif arithmetic_expr.variable_right == variable:
            constant_operand = arithmetic_expr.variable_left
        else:
            return None

        if isinstance(constant_operand, Constant):
            return Decimal(str(constant_operand.value))
        elif isinstance(constant_operand, Variable) and domain:
            # Check if this variable is effectively a constant
            if self._is_effectively_constant(constant_operand, domain):
                var_name = self.variable_manager.get_canonical_name(constant_operand)
                interval = domain.state.info.get(var_name)
                if interval:
                    return interval.lower_bound
        return None

    def _extract_constant_from_arithmetic_with_position(
        self, variable: Variable, arithmetic_expr: Binary, domain: Optional[IntervalDomain] = None
    ) -> Tuple[Optional[Decimal], bool]:
        """Extract constant value and whether variable is on the left side."""
        if arithmetic_expr.variable_left == variable:
            constant_operand = arithmetic_expr.variable_right
            is_variable_on_left = True
        elif arithmetic_expr.variable_right == variable:
            constant_operand = arithmetic_expr.variable_left
            is_variable_on_left = False
        else:
            return None, False

        if isinstance(constant_operand, Constant):
            return Decimal(str(constant_operand.value)), is_variable_on_left
        elif isinstance(constant_operand, Variable) and domain:
            # Check if this variable is effectively a constant
            if self._is_effectively_constant(constant_operand, domain):
                var_name = self.variable_manager.get_canonical_name(constant_operand)
                interval = domain.state.info.get(var_name)
                if interval:
                    return interval.lower_bound, is_variable_on_left
        return None, False

    def _apply_constraint_to_variable(
        self,
        variable: Variable,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint to variable and update domain."""
        var_name = self.variable_manager.get_canonical_name(variable)
        current_interval = self.variable_manager.create_interval_for_variable(
            variable, domain.state.info
        )

        new_interval = current_interval.deep_copy()
        IntervalCalculator.apply_comparison_constraint_to_interval(
            new_interval, constraint_value, op_type
        )

        if IntervalCalculator.is_valid_interval(new_interval):
            domain.state.info[var_name] = new_interval
        else:
            logger.error(f"\tInvalid interval: {new_interval}")

    def _solve_multiplication_constraint(
        self,
        variable: Variable,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x * constant > value for x."""
        constant_value = self._extract_constant_from_arithmetic(variable, arithmetic_expr, domain)
        if constant_value is None or constant_value == 0:
            return  # Multiplication by zero

        constraint_value = constraint_interval.lower_bound
        raw_value = constraint_value / constant_value

        new_constraint_value, new_op_type = self._solve_multiplication_constraint_core(
            constant_value, raw_value, op_type
        )

        self._apply_constraint_to_variable(variable, new_constraint_value, new_op_type, domain)

    def _solve_multiplication_constraint_core(
        self, constant_value: Decimal, raw_value: Decimal, op_type: BinaryType
    ) -> Tuple[Decimal, BinaryType]:
        """Core logic for solving multiplication constraints with proper integer arithmetic."""
        # Determine if we need to flip the operator based on constant sign
        flip_operator = constant_value < 0

        if op_type == BinaryType.LESS:
            if not flip_operator:
                # x * pos < value => x < value/pos
                # For integers: x < 50.0 means x <= 49
                new_constraint_value = Decimal(str(math.floor(raw_value) - 1))
                new_op_type = BinaryType.LESS_EQUAL
            else:
                # x * neg < value => x > value/neg (flipped)
                # For integers: x > 50.0 means x >= 51
                new_constraint_value = Decimal(str(math.floor(raw_value) + 1))
                new_op_type = BinaryType.GREATER_EQUAL
        elif op_type == BinaryType.LESS_EQUAL:
            if not flip_operator:
                # x * pos <= value => x <= value/pos
                new_constraint_value = Decimal(str(math.floor(raw_value)))
                new_op_type = BinaryType.LESS_EQUAL
            else:
                # x * neg <= value => x >= value/neg (flipped)
                new_constraint_value = Decimal(str(math.ceil(raw_value)))
                new_op_type = BinaryType.GREATER_EQUAL
        elif op_type == BinaryType.GREATER:
            if not flip_operator:
                # x * pos > value => x > value/pos
                # For integers: x > 50.0 means x >= 51
                new_constraint_value = Decimal(str(math.floor(raw_value) + 1))
                new_op_type = BinaryType.GREATER_EQUAL
            else:
                # x * neg > value => x < value/neg (flipped)
                # For integers: x < 50.0 means x <= 49
                new_constraint_value = Decimal(str(math.floor(raw_value) - 1))
                new_op_type = BinaryType.LESS_EQUAL
        elif op_type == BinaryType.GREATER_EQUAL:
            if not flip_operator:
                # x * pos >= value => x >= value/pos
                new_constraint_value = Decimal(str(math.ceil(raw_value)))
                new_op_type = BinaryType.GREATER_EQUAL
            else:
                # x * neg >= value => x <= value/neg (flipped)
                new_constraint_value = Decimal(str(math.floor(raw_value)))
                new_op_type = BinaryType.LESS_EQUAL
        else:
            new_constraint_value = raw_value
            new_op_type = op_type if not flip_operator else self.flip_comparison_operator(op_type)

        return new_constraint_value, new_op_type

    def _solve_division_constraint(
        self,
        variable: Variable,
        arithmetic_expr: Binary,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x / constant > value for x."""
        constant_value, is_variable_on_left = self._extract_constant_from_arithmetic_with_position(
            variable, arithmetic_expr, domain
        )

        if constant_value is None:
            logger.error(f"\tConstant value is None")
            return

        constraint_value = constraint_interval.lower_bound

        if is_variable_on_left:
            # x / constant > value
            if constant_value > 0:
                # Solve: x / constant > value => x > value * constant
                raw_value = constraint_value * constant_value
                new_constraint_value, new_op_type = self._solve_division_constraint_core(
                    raw_value, op_type, flip_operator=False, negative_constant=False
                )
            else:  # constant_value < 0
                # Solve: x / negative_constant > value => x < value * negative_constant
                # This flips the inequality because dividing by negative flips the sign
                raw_value = constraint_value * constant_value
                new_constraint_value, new_op_type = self._solve_division_constraint_core(
                    raw_value, op_type, flip_operator=True, negative_constant=True
                )
        else:
            # constant / x > value
            if constant_value > 0:
                # Solve: constant / x > value => x < constant / value
                raw_value = constant_value / constraint_value
                new_constraint_value, new_op_type = self._solve_division_constraint_core(
                    raw_value, op_type, flip_operator=True, negative_constant=False
                )
            else:  # constant_value < 0
                # Solve: negative_constant / x > value => x > negative_constant / value
                raw_value = constant_value / constraint_value
                new_constraint_value, new_op_type = self._solve_division_constraint_core(
                    raw_value, op_type, flip_operator=False, negative_constant=True
                )

        self._apply_constraint_to_variable(variable, new_constraint_value, new_op_type, domain)

    def _solve_division_constraint_core(
        self,
        raw_value: Decimal,
        op_type: BinaryType,
        flip_operator: bool,
        negative_constant: bool = False,
    ) -> Tuple[Decimal, BinaryType]:
        """Core logic for solving division constraints with proper integer arithmetic."""

        if op_type == BinaryType.LESS:
            if not flip_operator:
                # x < value -> x <= value - 1 (for integers)
                new_constraint_value = Decimal(str(math.floor(raw_value) - 1))
                new_op_type = BinaryType.LESS_EQUAL
            else:
                # x > value => x >= value + 1 (flipped, for integers)
                new_constraint_value = Decimal(str(math.floor(raw_value) + 1))
                new_op_type = BinaryType.GREATER_EQUAL
        elif op_type == BinaryType.LESS_EQUAL:
            if not flip_operator:
                # x <= value => x <= value
                new_constraint_value = Decimal(str(math.floor(raw_value)))
                new_op_type = BinaryType.LESS_EQUAL
            else:
                # x >= value => x >= value (flipped)
                new_constraint_value = Decimal(str(math.ceil(raw_value)))
                new_op_type = BinaryType.GREATER_EQUAL
        elif op_type == BinaryType.GREATER:
            if not flip_operator:
                # x > value => x >= value + 1 (for integers)
                new_constraint_value = Decimal(str(math.floor(raw_value) + 1))
                new_op_type = BinaryType.GREATER_EQUAL
            else:
                # x < value => x <= value - 1 (flipped, for integers)
                new_constraint_value = Decimal(str(math.floor(raw_value) - 1))
                new_op_type = BinaryType.LESS_EQUAL
        elif op_type == BinaryType.GREATER_EQUAL:
            if not flip_operator:
                # x >= value => x >= value
                new_constraint_value = Decimal(str(math.ceil(raw_value)))
                new_op_type = BinaryType.GREATER_EQUAL
            else:
                # x <= value => x <= value (flipped)
                new_constraint_value = Decimal(str(math.floor(raw_value)))
                new_op_type = BinaryType.LESS_EQUAL
        else:
            new_constraint_value = raw_value
            new_op_type = op_type if not flip_operator else self.flip_comparison_operator(op_type)

        return new_constraint_value, new_op_type
