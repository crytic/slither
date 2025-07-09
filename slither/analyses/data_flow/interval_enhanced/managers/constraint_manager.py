from decimal import Decimal
from typing import Dict, List, Optional, Union

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.arithmetic_solver_manager import (
    ArithmeticSolverManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_application_manager import (
    ConstraintApplicationManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_range_manager import (
    ConstraintRangeManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ConstraintManager:
    """Main orchestrator for constraint management in interval analysis."""

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
        self._temp_var_mappings: Dict[str, Binary] = (
            {}
        )  # Track temp vars to their source expressions

        # Initialize component managers
        self.variable_manager = VariableManager()
        self.operand_analyzer = OperandAnalysisManager(self.variable_manager)
        self.constraint_range_manager = ConstraintRangeManager(self.variable_manager)
        self.arithmetic_solver = ArithmeticSolverManager(
            self.operand_analyzer, self.constraint_range_manager
        )
        self.constraint_application_manager = ConstraintApplicationManager(
            self.operand_analyzer,
            self.constraint_range_manager,
            self.arithmetic_solver,
            self.variable_manager,
        )

    # Core constraint storage methods
    def add_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Add a pending constraint for a variable"""
        self._pending_constraints[var_name] = constraint

    def remove_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Remove and return a constraint for a variable"""
        constraint = self._pending_constraints.pop(var_name, None)
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

    # Temporary variable mapping methods
    def add_temp_var_mapping(self, temp_var_name: str, source_expression: Binary) -> None:
        """Track a temporary variable's source arithmetic expression."""
        self._temp_var_mappings[temp_var_name] = source_expression

    def get_temp_var_mapping(self, temp_var_name: str) -> Optional[Binary]:
        """Get the source expression for a temporary variable."""
        return self._temp_var_mappings.get(temp_var_name)

    def has_temp_var_mapping(self, temp_var_name: str) -> bool:
        """Check if a temporary variable has a source expression mapping."""
        return temp_var_name in self._temp_var_mappings

    # Constraint application orchestration
    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition variable"""
        variable_name = self.variable_manager.get_variable_name(condition_variable)
        constraint = self.get_constraint(variable_name)

        if isinstance(constraint, Binary):
            self.apply_constraint_from_binary_condition(constraint, domain)
        elif isinstance(constraint, Variable):
            self.apply_constraint_from_variable(constraint, domain)

    def apply_constraint_from_binary_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from a binary condition"""
        if condition.type in self.COMPARISON_OPERATORS:
            self.apply_constraint_from_comparison_condition(condition, domain)

    def apply_constraint_from_comparison_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from comparison condition by refining variable bounds"""
        # Get the left and right operands
        left_operand = condition.variable_left
        right_operand = condition.variable_right

        left_is_variable = not self.operand_analyzer.is_operand_constant(left_operand, domain)
        right_is_variable = not self.operand_analyzer.is_operand_constant(right_operand, domain)

        if left_is_variable and not right_is_variable:
            # Check if this is a temporary variable with an arithmetic mapping
            if isinstance(left_operand, Variable):
                left_var_name = self.variable_manager.get_variable_name(left_operand)
                if self.has_temp_var_mapping(left_var_name):
                    source_expr = self.get_temp_var_mapping(left_var_name)
                    if source_expr:
                        # Handle as arithmetic constraint
                        if isinstance(right_operand, Constant):
                            self.arithmetic_solver.handle_arithmetic_comparison_constraint(
                                source_expr, Decimal(right_operand.value), condition.type, domain
                            )
                else:
                    # Handle as regular variable constraint
                    self.constraint_application_manager.apply_constraint_from_comparison_condition(
                        condition, domain
                    )

        elif right_is_variable and not left_is_variable:
            # Check if this is a temporary variable with an arithmetic mapping
            if isinstance(right_operand, Variable):
                right_var_name = self.variable_manager.get_variable_name(right_operand)
                if self.has_temp_var_mapping(right_var_name):
                    source_expr = self.get_temp_var_mapping(right_var_name)
                    if source_expr:
                        # Handle as arithmetic constraint
                        if isinstance(left_operand, Constant):
                            flipped_op_type = (
                                self.constraint_range_manager.flip_comparison_operator(
                                    condition.type
                                )
                            )
                            self.arithmetic_solver.handle_arithmetic_comparison_constraint(
                                source_expr, Decimal(left_operand.value), flipped_op_type, domain
                            )
                else:
                    # Handle as regular variable constraint
                    self.constraint_application_manager.apply_constraint_from_comparison_condition(
                        condition, domain
                    )

        elif left_is_variable and right_is_variable:
            # Handle as variable-to-variable comparison
            self.constraint_application_manager.apply_constraint_from_comparison_condition(
                condition, domain
            )

        else:
            # Case 4: constant < constant, constant > constant, etc.
            # This is a compile-time constant expression, no variables to constrain
            logger.debug(f"Constant comparison: {left_operand} {condition.type} {right_operand}")
