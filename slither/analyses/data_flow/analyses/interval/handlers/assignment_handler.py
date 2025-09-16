from decimal import Decimal

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class AssignmentHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:

        if operation.lvalue is None:
            logger.error("Assignment lvalue is None")
            raise ValueError("Assignment lvalue is None")

        written_variable: Variable = operation.lvalue
        right_value = operation.rvalue

        if isinstance(right_value, TemporaryVariable):
            self._handle_temporary_assignment(written_variable, right_value, domain)
        elif isinstance(right_value, Constant):
            self._handle_constant_assignment(written_variable, right_value, domain)
        elif isinstance(right_value, Variable):
            self._handle_variable_assignment(written_variable, right_value, domain)

    def _handle_temporary_assignment(
        self,
        written_variable: Variable,
        source_variable: TemporaryVariable,
        domain: IntervalDomain,
    ) -> None:
        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)
        source_variable_name = self.variable_info_manager.get_variable_name(source_variable)

        # copy the temporary variable to the target variable
        source_range_variable = domain.state.get_range_variable(source_variable_name)

        if source_range_variable is None:
            logger.error(f"Source variable {source_variable_name} does not exist in domain state")
            raise ValueError(
                f"Source variable {source_variable_name} does not exist in domain state"
            )

        # Create range variable by copying from source
        range_variable = RangeVariable(
            interval_ranges=[ir.deep_copy() for ir in source_range_variable.get_interval_ranges()],
            valid_values=source_range_variable.get_valid_values().deep_copy(),
            invalid_values=source_range_variable.get_invalid_values().deep_copy(),
            var_type=written_variable_type,
        )

        # Store the relationship: local variable -> temporary variable
        domain.state.add_temp_var_mapping(written_variable_name, source_variable_name)

        domain.state.set_range_variable(written_variable_name, range_variable)

    def _handle_constant_assignment(
        self, written_variable: Variable, source_constant: Constant, domain: IntervalDomain
    ) -> None:
        value: Decimal = Decimal(str(source_constant.value))
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)
        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)

        if not self.variable_info_manager.is_type_numeric(written_variable_type):
            logger.warning(f"Assignment to non-numeric variable: {written_variable_name}")
            return

        range_variable = RangeVariable(
            interval_ranges=None,
            valid_values=ValueSet([value]),
            invalid_values=None,
            var_type=written_variable_type,
        )

        domain.state.set_range_variable(written_variable_name, range_variable)

    def _handle_variable_assignment(
        self, written_variable: Variable, source_variable: Variable, domain: IntervalDomain
    ) -> None:

        source_variable_name = self.variable_info_manager.get_variable_name(source_variable)
        if not domain.state.has_range_variable(source_variable_name):
            logger.error(f"Assignment from unknown variable: {source_variable_name}")
            raise ValueError(
                f"Source variable {source_variable_name} does not exist in domain state"
            )

        source_range_variable = domain.state.get_range_variable(source_variable_name)

        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)

        range_variable = RangeVariable(
            interval_ranges=[ir.deep_copy() for ir in source_range_variable.get_interval_ranges()],
            valid_values=source_range_variable.get_valid_values().deep_copy(),
            invalid_values=source_range_variable.get_invalid_values().deep_copy(),
            var_type=written_variable_type,
        )
        domain.state.set_range_variable(written_variable_name, range_variable)
