from decimal import Decimal

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import \
    IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.interval_refiner import \
    IntervalRefiner
from slither.analyses.data_flow.analyses.interval.managers.operand_analysis_manager import \
    OperandAnalysisManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType


class ArithmeticSolverManager:
    """Handles arithmetic constraint solving for interval analysis."""

    def __init__(self):
        self.operand_analyzer = OperandAnalysisManager()

    def solve_arithmetic_constraint(
        self,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve arithmetic constraint by propagating it back to the original variable."""
        # Extract variables from the arithmetic operation (e.g., x from x + 10)
        variables_in_arithmetic = self.operand_analyzer.extract_variables_from_arithmetic_operation(
            arithmetic_operation, domain
        )

        if not variables_in_arithmetic:
            return

        if len(variables_in_arithmetic) > 1:
            logger.warning(
                f"Multiple variables in arithmetic operation. Implement affine relations."
            )

        target_variable = variables_in_arithmetic[0]
        self._solve_constraint_for_variable(
            target_variable, arithmetic_operation, constraint_value, comparison_operator, domain
        )

    def _solve_constraint_for_variable(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Route constraint solving to the appropriate arithmetic operation handler."""
        if arithmetic_operation.type == BinaryType.ADDITION:
            self._solve_addition_constraint(
                target_variable, arithmetic_operation, constraint_value, comparison_operator, domain
            )
        elif arithmetic_operation.type == BinaryType.SUBTRACTION:
            self._solve_subtraction_constraint(
                target_variable, arithmetic_operation, constraint_value, comparison_operator, domain
            )
        elif arithmetic_operation.type == BinaryType.MULTIPLICATION:
            self._solve_multiplication_constraint(
                target_variable, arithmetic_operation, constraint_value, comparison_operator, domain
            )
        elif arithmetic_operation.type == BinaryType.DIVISION:
            self._solve_division_constraint(
                target_variable, arithmetic_operation, constraint_value, comparison_operator, domain
            )

    def _solve_addition_constraint(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x + constant > value for x."""
        # Extract the constant from the arithmetic operation (e.g., 10 from x + 10)
        constant_value = self.operand_analyzer.extract_constant_from_arithmetic(
            target_variable, arithmetic_operation, domain
        )
        if constant_value is None:
            return

        # Solve: x + constant > value => x > value - constant
        solved_constraint_value = constraint_value - constant_value
        solved_comparison_operator = comparison_operator  # Keep the same operator

        # Apply the solved constraint to the target variable
        var_name = self.operand_analyzer.variable_manager.get_variable_name(target_variable)
        range_var = domain.state.get_range_variable(var_name)
        if range_var is not None:
            # Adjust constraint for integer types
            adjusted_constraint_value, adjusted_operator = self._adjust_constraint_for_integer_type(
                target_variable, solved_constraint_value, solved_comparison_operator
            )
            IntervalRefiner.refine_variable_range(
                range_var, adjusted_constraint_value, adjusted_operator
            )

    def _solve_subtraction_constraint(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x - constant > value for x."""
        constant_value = self.operand_analyzer.extract_constant_from_arithmetic(
            target_variable, arithmetic_operation, domain
        )
        if constant_value is None:
            return

        # Check which side the variable is on to determine the solving approach
        if arithmetic_operation.variable_left == target_variable:
            # Case: x - constant > value => x > value + constant
            solved_constraint_value = constraint_value + constant_value
            solved_comparison_operator = comparison_operator  # Keep the same operator
        else:
            # Case: constant - x > value => x < constant - value
            solved_constraint_value = constant_value - constraint_value
            solved_comparison_operator = IntervalRefiner.flip_comparison_operator(
                comparison_operator
            )  # Flip the operator

        # Apply the solved constraint to the target variable
        var_name = self.operand_analyzer.variable_manager.get_variable_name(target_variable)
        range_var = domain.state.get_range_variable(var_name)
        if range_var is not None:
            # Adjust constraint for integer types
            adjusted_constraint_value, adjusted_operator = self._adjust_constraint_for_integer_type(
                target_variable, solved_constraint_value, solved_comparison_operator
            )
            IntervalRefiner.refine_variable_range(
                range_var, adjusted_constraint_value, adjusted_operator
            )

    def _solve_multiplication_constraint(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x * constant > value for x."""
        constant_value = self.operand_analyzer.extract_constant_from_arithmetic(
            target_variable, arithmetic_operation, domain
        )
        if constant_value is None or constant_value == 0:
            return  # Skip multiplication by zero

        # Solve: x * constant > value => x > value / constant (if constant > 0)
        # or x < value / constant (if constant < 0)
        solved_constraint_value = constraint_value / constant_value

        # Handle sign of constant: positive keeps operator, negative flips it
        if constant_value > 0:
            solved_comparison_operator = comparison_operator  # Keep the same operator
        else:
            solved_comparison_operator = IntervalRefiner.flip_comparison_operator(
                comparison_operator
            )  # Flip the operator

        # Apply the solved constraint to the target variable
        var_name = self.operand_analyzer.variable_manager.get_variable_name(target_variable)
        range_var = domain.state.get_range_variable(var_name)
        if range_var is not None:
            # Adjust constraint for integer types
            adjusted_constraint_value, adjusted_operator = self._adjust_constraint_for_integer_type(
                target_variable, solved_constraint_value, solved_comparison_operator
            )
            IntervalRefiner.refine_variable_range(
                range_var, adjusted_constraint_value, adjusted_operator
            )

    def _solve_division_constraint(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x / constant > value for x."""
        constant_value, is_variable_on_left = (
            self.operand_analyzer.extract_constant_from_arithmetic_with_position(
                target_variable, arithmetic_operation, domain
            )
        )
        if constant_value is None or constant_value == 0:
            return  # Skip division by zero

        if is_variable_on_left:
            # Case: x / constant > value => x > value * constant (if constant > 0)
            # or x < value * constant (if constant < 0)
            solved_constraint_value = constraint_value * constant_value

            # Handle sign of constant: positive keeps operator, negative flips it
            if constant_value > 0:
                solved_comparison_operator = comparison_operator  # Keep the same operator
            else:
                solved_comparison_operator = IntervalRefiner.flip_comparison_operator(
                    comparison_operator
                )  # Flip the operator
        else:
            # Case: constant / x > value => x < constant / value (if value > 0)
            # or x > constant / value (if value < 0)
            if constraint_value == 0:
                return  # Skip division by zero

            solved_constraint_value = constant_value / constraint_value

            # Handle sign of constraint value: positive flips operator, negative keeps it
            if constraint_value > 0:
                solved_comparison_operator = IntervalRefiner.flip_comparison_operator(
                    comparison_operator
                )  # Flip the operator
            else:
                solved_comparison_operator = comparison_operator  # Keep the same operator

        # Apply the solved constraint to the target variable
        var_name = self.operand_analyzer.variable_manager.get_variable_name(target_variable)
        range_var = domain.state.get_range_variable(var_name)
        if range_var is not None:
            # Adjust constraint for integer types
            adjusted_constraint_value, adjusted_operator = self._adjust_constraint_for_integer_type(
                target_variable, solved_constraint_value, solved_comparison_operator
            )
            IntervalRefiner.refine_variable_range(
                range_var, adjusted_constraint_value, adjusted_operator
            )

    def _adjust_constraint_for_integer_type(
        self,
        target_variable: Variable,
        constraint_value: Decimal,
        comparison_operator: BinaryType,
    ) -> tuple[Decimal, BinaryType]:
        """Adjust constraint for integer types (e.g., x < 12.5 becomes x <= 12 for integers)."""
        # Check if the variable is an integer type
        if not self.operand_analyzer.variable_manager.is_type_numeric(target_variable.type):
            return constraint_value, comparison_operator

        # For integer types, adjust constraints involving fractional values
        if constraint_value % 1 != 0:  # If constraint value is not a whole number
            if comparison_operator == BinaryType.LESS:
                # x < 12.5 becomes x <= 12 for integers
                return Decimal(int(constraint_value)), BinaryType.LESS_EQUAL
            elif comparison_operator == BinaryType.GREATER:
                # x > 12.5 becomes x >= 13 for integers
                return Decimal(int(constraint_value) + 1), BinaryType.GREATER_EQUAL
            elif comparison_operator == BinaryType.LESS_EQUAL:
                # x <= 12.5 becomes x <= 12 for integers
                return Decimal(int(constraint_value)), BinaryType.LESS_EQUAL
            elif comparison_operator == BinaryType.GREATER_EQUAL:
                # x >= 12.5 becomes x >= 13 for integers
                return Decimal(int(constraint_value) + 1), BinaryType.GREATER_EQUAL

        return constraint_value, comparison_operator
