from decimal import Decimal

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_range_manager import (
    ConstraintRangeManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType


class ArithmeticSolverManager:
    """Handles arithmetic constraint solving for interval analysis."""

    def __init__(
        self,
        operand_analyzer_manager: OperandAnalysisManager,
        constraint_range_manager: ConstraintRangeManager,
    ):
        self.operand_analyzer_manager = operand_analyzer_manager
        self.constraint_range_manager = constraint_range_manager

    def handle_arithmetic_comparison_constraint(
        self,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Handle constraint propagation for arithmetic operation in comparisons."""
        # Extract variables from the arithmetic operation
        variables_in_operation = (
            self.operand_analyzer_manager.extract_variables_from_arithmetic_operation(
                arithmetic_operation, domain
            )
        )

        if not variables_in_operation:
            return

        # For now, handle simple cases with one variable
        if len(variables_in_operation) == 1:
            var = variables_in_operation[0]
            self._propagate_arithmetic_constraint_to_variable(
                var, arithmetic_operation, constraint_value, op_type, domain
            )
        else:
            logger.warning(
                f"\tMultiple variables in arithmetic operation. Implement affine relations."
            )

    def _propagate_arithmetic_constraint_to_variable(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Propagate arithmetic constraint back to the original variable."""
        if arithmetic_operation.type == BinaryType.ADDITION:
            self._solve_addition_constraint(
                variable, arithmetic_operation, constraint_value, op_type, domain
            )
        elif arithmetic_operation.type == BinaryType.SUBTRACTION:
            self._solve_subtraction_constraint(
                variable, arithmetic_operation, constraint_value, op_type, domain
            )
        elif arithmetic_operation.type == BinaryType.DIVISION:
            self._solve_division_constraint(
                variable, arithmetic_operation, constraint_value, op_type, domain
            )
        elif arithmetic_operation.type == BinaryType.MULTIPLICATION:
            self._solve_multiplication_constraint(
                variable, arithmetic_operation, constraint_value, op_type, domain
            )

    def _solve_addition_constraint(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x + constant > value for x."""
        constant_value = self.operand_analyzer_manager.extract_constant_from_arithmetic(
            variable, arithmetic_operation, domain
        )
        if constant_value is None:
            return

        # Solve: x + constant > value => x > value - constant
        new_constraint_value = constraint_value - constant_value
        new_op_type = op_type  # Keep the same operator

        self.constraint_range_manager.apply_constraint_to_variable_with_value(
            variable, new_constraint_value, new_op_type, domain
        )

    def _solve_subtraction_constraint(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x - constant > value for x."""
        constant_value, is_variable_on_left = (
            self.operand_analyzer_manager.extract_constant_from_arithmetic_with_position(
                variable, arithmetic_operation, domain
            )
        )
        if constant_value is None:
            return

        if is_variable_on_left:
            # x - constant > value => x > value + constant
            new_constraint_value = constraint_value + constant_value
            new_op_type = op_type  # Keep the same operator
        else:
            # constant - x > value => x < constant - value
            new_constraint_value = constant_value - constraint_value
            new_op_type = self.constraint_range_manager.flip_comparison_operator(
                op_type
            )  # Flip the operator

        self.constraint_range_manager.apply_constraint_to_variable_with_value(
            variable, new_constraint_value, new_op_type, domain
        )

    def _solve_multiplication_constraint(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x * constant > value for x."""
        constant_value = self.operand_analyzer_manager.extract_constant_from_arithmetic(
            variable, arithmetic_operation, domain
        )
        if constant_value is None or constant_value == 0:
            return  # Multiplication by zero

        # Solve: x * constant > value => x > value / constant (if constant > 0)
        # or x < value / constant (if constant < 0)
        new_constraint_value = constraint_value / constant_value

        if constant_value > 0:
            new_op_type = op_type  # Keep the same operator
        else:
            new_op_type = self.constraint_range_manager.flip_comparison_operator(
                op_type
            )  # Flip the operator

        self.constraint_range_manager.apply_constraint_to_variable_with_value(
            variable, new_constraint_value, new_op_type, domain
        )

    def _solve_division_constraint(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Solve constraint like x / constant > value for x."""
        constant_value, is_variable_on_left = (
            self.operand_analyzer_manager.extract_constant_from_arithmetic_with_position(
                variable, arithmetic_operation, domain
            )
        )
        if constant_value is None or constant_value == 0:
            return  # Division by zero

        if is_variable_on_left:
            # x / constant > value => x > value * constant (if constant > 0)
            # or x < value * constant (if constant < 0)
            new_constraint_value = constraint_value * constant_value

            if constant_value > 0:
                new_op_type = op_type  # Keep the same operator
            else:
                new_op_type = self.constraint_range_manager.flip_comparison_operator(
                    op_type
                )  # Flip the operator
        else:
            # constant / x > value => x < constant / value (if value > 0)
            # or x > constant / value (if value < 0)
            if constraint_value == 0:
                return  # Division by zero

            new_constraint_value = constant_value / constraint_value

            if constraint_value > 0:
                new_op_type = self.constraint_range_manager.flip_comparison_operator(
                    op_type
                )  # Flip the operator
            else:
                new_op_type = op_type  # Keep the same operator

        self.constraint_range_manager.apply_constraint_to_variable_with_value(
            variable, new_constraint_value, new_op_type, domain
        )
