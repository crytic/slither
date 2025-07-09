from decimal import Decimal
from typing import List, Optional, Union

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class OperandAnalysisManager:
    """Handles operand type checking and value extraction for constraint analysis."""

    def __init__(self, variable_manager: VariableManager):
        self.variable_manager = variable_manager

    def is_operand_constant(
        self, operand: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain
    ) -> bool:
        """Check if an operand is a constant"""
        if isinstance(operand, Constant):
            return True
        if isinstance(operand, Variable):
            var_name = self.variable_manager.get_variable_name(operand)
            if var_name in domain.state.info:
                var_info = domain.state.info[var_name]
                # Check if the variable has exactly one valid value (effectively a constant)
                if len(var_info.get_valid_values()) == 1 and not var_info.interval_ranges:
                    return True
        return False

    def extract_variables_from_arithmetic_operation(
        self, arithmetic_operation: Binary, domain: Optional[IntervalDomain] = None
    ) -> List[Variable]:
        """Extract all variables from an arithmetic expression."""
        variables: List[Variable] = []

        def extract_from_operand(operand):
            if isinstance(operand, Variable):
                # Check if this variable is effectively a constant
                if domain and self.is_operand_constant(operand, domain):
                    pass  # Skip constants
                else:
                    variables.append(operand)

        extract_from_operand(arithmetic_operation.variable_left)
        extract_from_operand(arithmetic_operation.variable_right)

        return variables

    def extract_constant_from_arithmetic(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        domain: Optional[IntervalDomain] = None,
    ) -> Optional[Decimal]:
        """Extract constant value from arithmetic expression where variable is one operand."""
        if arithmetic_operation.variable_left == variable:
            constant_operand = arithmetic_operation.variable_right
        elif arithmetic_operation.variable_right == variable:
            constant_operand = arithmetic_operation.variable_left
        else:
            return None

        if isinstance(constant_operand, Constant):
            return Decimal(str(constant_operand.value))
        elif isinstance(constant_operand, Variable) and domain:
            # Check if this variable is effectively a constant
            if self.is_operand_constant(constant_operand, domain):
                var_name = self.variable_manager.get_variable_name(constant_operand)
                if var_name in domain.state.info:
                    state_info = domain.state.info[var_name]
                    if not state_info.valid_values.is_empty():
                        # Return the first valid value as the constant
                        return list(state_info.valid_values)[0]
        return None

    def extract_constant_from_arithmetic_with_position(
        self,
        variable: Variable,
        arithmetic_operation: Binary,
        domain: Optional[IntervalDomain] = None,
    ) -> tuple[Optional[Decimal], bool]:
        """Extract constant value and whether variable is on the left side."""
        if arithmetic_operation.variable_left == variable:
            constant_operand = arithmetic_operation.variable_right
            is_variable_on_left = True
        elif arithmetic_operation.variable_right == variable:
            constant_operand = arithmetic_operation.variable_left
            is_variable_on_left = False
        else:
            return None, False

        if isinstance(constant_operand, Constant):
            return Decimal(str(constant_operand.value)), is_variable_on_left
        elif isinstance(constant_operand, Variable) and domain:
            # Check if this variable is effectively a constant
            if not self.is_operand_constant(constant_operand, domain):
                return None, False
            var_name = self.variable_manager.get_variable_name(constant_operand)
            if var_name not in domain.state.info:
                return None, False
            state_info = domain.state.info[var_name]
            if state_info.valid_values.is_empty():
                return None, False
            # Return the first valid value as the constant
            return list(state_info.valid_values)[0], is_variable_on_left
        return None, False
