"""Return operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.return_operation import Return
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    constant_to_term,
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.core.solidity_types.elementary_type import ElementaryType

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class ReturnHandler(BaseOperationHandler):
    """Handler for return operations.

    When a return value is a constant, creates a tracked variable constrained
    to that constant. This enables interprocedural analysis to extract the
    return value from functions that return constants directly.
    """

    def handle(
        self,
        operation: Return,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process return operation by tracking constant return values."""
        if not operation.values:
            return

        for return_value in operation.values:
            self._track_return_value(return_value, domain)

    def _track_return_value(
        self,
        return_value,
        domain: "IntervalDomain",
    ) -> None:
        """Track a single return value if it's a constant."""
        if not isinstance(return_value, Constant):
            return

        value_type = return_value.type
        if not isinstance(value_type, ElementaryType):
            return

        constant_value = return_value.value
        if not isinstance(constant_value, int):
            return

        return_name = get_variable_name(return_value)
        bit_width = get_bit_width(value_type)
        sort = type_to_sort(value_type)
        is_signed = is_signed_type(value_type)

        return_var = TrackedSMTVariable.create(
            self.solver, return_name, sort, is_signed=is_signed, bit_width=bit_width
        )

        constant_term = constant_to_term(self.solver, constant_value, bit_width)
        self.solver.assert_constraint(return_var.term == constant_term)

        domain.state.set_variable(return_name, return_var)
