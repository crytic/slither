from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.internal_dynamic_call import InternalDynamicCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis


from IPython import embed


class InternalDynamicCallHandler:
    def __init__(self, constraint_manager: ConstraintManager = None):
        self.constraint_manager = constraint_manager or ConstraintManager()
        self.variable_info_manager = VariableInfoManager()

    def handle_internal_dynamic_call(
        self, node: Node, domain: IntervalDomain, operation: InternalDynamicCall
    ) -> None:
        """Handle internal dynamic function calls (function pointers)."""
        logger.debug(f"Processing InternalDynamicCall: {operation}")

        # Early return if no return value expected
        if not operation.lvalue:
            logger.debug("InternalDynamicCall has no lvalue, skipping result handling")
            return

        lvalue = operation.lvalue
        function_pointer = operation.function
        function_type = operation.function_type

        result_var_name = self.variable_info_manager.get_variable_name(lvalue)
        result_type = self.variable_info_manager.get_variable_type(lvalue)

        logger.debug(f"Dynamic call result: {result_var_name} of type {result_type}")

        # Create conservative range since we can't determine exact function at runtime
        range_variable = self._create_dynamic_call_result_range_variable(
            result_type, function_type, domain
        )

        domain.state.set_range_variable(result_var_name, range_variable)

        # Don't store InternalDynamicCall operations as constraints
        # Only comparison operations should be stored as constraints
        # InternalDynamicCall results are operation results, not comparison constraints

        logger.debug(f"Created range variable for dynamic call result: {result_var_name}")

    def _create_dynamic_call_result_range_variable(
        self, result_type, function_type, domain: IntervalDomain
    ) -> RangeVariable:
        """Create a conservative range variable for dynamic call results."""

        if self.variable_info_manager.is_type_numeric(result_type):
            # For numeric types, use full type range (conservative)
            return RangeVariable(
                interval_ranges=[
                    IntervalRange(
                        lower_bound=result_type.min,
                        upper_bound=result_type.max,
                    )
                ],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )
        else:
            # For non-numeric types, create placeholder
            return RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )
