from decimal import Decimal
from typing import List, Optional, Union

from slither.analyses.data_flow.analyses.interval.analysis.domain import \
    IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import \
    VariableInfoManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary
from slither.slithir.variables.constant import Constant


class OperandAnalysisManager:
    """Handles operand type checking and value extraction for constraint analysis."""

    def __init__(self):
        self.variable_manager = VariableInfoManager()

    def is_operand_constant(
        self, operand: Union[Variable, Constant], domain: IntervalDomain
    ) -> bool:
        """Check if an operand is effectively a constant (literal or single-value variable)."""
        if isinstance(operand, Constant):
            return True

        operand_var_name = self.variable_manager.get_variable_name(operand)
        if not domain.state.has_range_variable(operand_var_name):
            return False

        operand_range_var = domain.state.get_range_variable(operand_var_name)
        # Check if the variable has exactly one valid value (effectively a constant)
        if (
            len(operand_range_var.get_valid_values()) == 1
            and not operand_range_var.get_interval_ranges()
        ):
            return True
        return False

    def extract_variables_from_arithmetic_operation(
        self, arithmetic_operation: Binary, domain: Optional[IntervalDomain] = None
    ) -> List[Variable]:
        """Extract all non-constant variables from an arithmetic expression."""
        non_constant_variables: List[Variable] = []

        def extract_from_operand(operand):
            if isinstance(operand, Variable):
                # Skip variables that are effectively constants (single values)
                if domain and self.is_operand_constant(operand, domain):
                    pass  # Skip constants
                else:
                    non_constant_variables.append(operand)

        # Extract variables from both operands of the arithmetic operation
        extract_from_operand(arithmetic_operation.variable_left)
        extract_from_operand(arithmetic_operation.variable_right)

        return non_constant_variables

    def extract_constant_from_arithmetic(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        domain: Optional[IntervalDomain] = None,
    ) -> Optional[Decimal]:
        """Extract constant value from arithmetic expression where target_variable is one operand."""
        # Find the other operand (which should be the constant)
        if arithmetic_operation.variable_left == target_variable:
            other_operand = arithmetic_operation.variable_right
        elif arithmetic_operation.variable_right == target_variable:
            other_operand = arithmetic_operation.variable_left
        else:
            return None

        if isinstance(other_operand, Constant):
            return Decimal(str(other_operand.value))
        elif isinstance(other_operand, Variable) and domain:
            # Check if this variable is effectively a constant (single value)
            if self.is_operand_constant(other_operand, domain):
                other_var_name = self.variable_manager.get_variable_name(other_operand)
                if domain.state.has_range_variable(other_var_name):
                    other_range_var = domain.state.get_range_variable(other_var_name)
                    valid_values = other_range_var.get_valid_values()
                    if valid_values:
                        # Return the first valid value as the constant
                        return list(valid_values)[0]
        return None

    def extract_constant_from_arithmetic_with_position(
        self,
        target_variable: Variable,
        arithmetic_operation: Binary,
        domain: Optional[IntervalDomain] = None,
    ) -> tuple[Optional[Decimal], bool]:
        """Extract constant value and whether target_variable is on the left side of the operation."""
        # Determine which side the target variable is on and get the other operand
        if arithmetic_operation.variable_left == target_variable:
            other_operand = arithmetic_operation.variable_right
            is_target_variable_on_left = True
        elif arithmetic_operation.variable_right == target_variable:
            other_operand = arithmetic_operation.variable_left
            is_target_variable_on_left = False
        else:
            return None, False

        if isinstance(other_operand, Constant):
            return Decimal(str(other_operand.value)), is_target_variable_on_left
        elif isinstance(other_operand, Variable) and domain:
            # Check if this variable is effectively a constant (single value)
            if not self.is_operand_constant(other_operand, domain):
                return None, False
            other_var_name = self.variable_manager.get_variable_name(other_operand)
            if not domain.state.has_range_variable(other_var_name):
                return None, False
            other_range_var = domain.state.get_range_variable(other_var_name)
            valid_values = other_range_var.get_valid_values()
            if not valid_values:
                return None, False
            # Return the first valid value as the constant
            return list(valid_values)[0], is_target_variable_on_left
        return None, False
