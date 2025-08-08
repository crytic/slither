from decimal import Decimal
from typing import Optional

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class AssignmentHandler:
    def __init__(self, constraint_manager: ConstraintManager, widening_manager):
        self.variable_manager = VariableManager()
        self.constraint_manager = constraint_manager
        self.widening_manager = widening_manager

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        if operation.lvalue is None:
            return

        written_variable: Variable = operation.lvalue
        right_value = operation.rvalue
        writing_variable_name: str = self.variable_manager.get_variable_name(written_variable)

        if isinstance(right_value, TemporaryVariable):
            self._handle_temporary_assignment(
                writing_variable_name, right_value, written_variable, domain
            )
            return
        elif isinstance(right_value, Constant):
            self._handle_constant_assignment(
                writing_variable_name, right_value, written_variable, domain
            )
        elif isinstance(right_value, Variable):
            self._handle_variable_assignment(
                writing_variable_name, right_value, written_variable, domain
            )

    def _handle_temporary_assignment(
        self,
        var_name: str,
        temporary: TemporaryVariable,
        target_var: Variable,
        domain: IntervalDomain,
    ) -> None:
        temporary_var_name = self.variable_manager.get_variable_name(temporary)
        target_type = self.variable_manager.get_variable_type(target_var)

        # Copy state information from temporary variable to target variable
        if temporary_var_name in domain.state.info:
            source_state_info = domain.state.info[temporary_var_name]

            # Deep copy all components with target variable's type
            state_info = StateInfo(
                interval_ranges=[ir.deep_copy() for ir in source_state_info.interval_ranges],
                valid_values=source_state_info.valid_values.deep_copy(),
                invalid_values=source_state_info.invalid_values.deep_copy(),
                var_type=target_type if target_type else ElementaryType("uint256"),
            )

            domain.state.info[var_name] = state_info

        # Handle constraint propagation
        if self.constraint_manager.has_constraint(temporary_var_name):
            constraint = self.constraint_manager.get_constraint(temporary_var_name)
            if constraint is not None:
                self.constraint_manager.add_constraint(var_name=var_name, constraint=constraint)
            self.constraint_manager.remove_constraint(temporary_var_name)

    def _handle_constant_assignment(
        self, var_name: str, constant: Constant, target_var: Variable, domain: IntervalDomain
    ) -> None:
        value: Decimal = Decimal(str(constant.value))
        target_type: Optional[ElementaryType] = self.variable_manager.get_variable_type(target_var)

        # Check if this variable has been widened - if so, don't add valid values
        valid_values = SingleValues()
        if not self.widening_manager.is_variable_widened(var_name):
            valid_values.add(value)

        # Create empty interval ranges and invalid values
        interval_ranges = []
        invalid_values = SingleValues()

        # Handle None type case
        if target_type is None:
            target_type = ElementaryType("uint256")

        state_info = StateInfo(
            interval_ranges=interval_ranges,
            valid_values=valid_values,
            invalid_values=invalid_values,
            var_type=target_type,
        )

        domain.state.info[var_name] = state_info

    def _handle_variable_assignment(
        self, var_name: str, source_var: Variable, target_var: Variable, domain: IntervalDomain
    ) -> None:
        source_var_name = self.variable_manager.get_variable_name(source_var)
        target_type = self.variable_manager.get_variable_type(target_var)

        # Look up source variable's state info
        if source_var_name in domain.state.info:
            source_state_info = domain.state.info[source_var_name]

            # Deep copy all components with target variable's type
            state_info = StateInfo(
                interval_ranges=[ir.deep_copy() for ir in source_state_info.interval_ranges],
                valid_values=source_state_info.valid_values.deep_copy(),
                invalid_values=source_state_info.invalid_values.deep_copy(),
                var_type=target_type if target_type else ElementaryType("uint256"),
            )

        domain.state.info[var_name] = state_info
