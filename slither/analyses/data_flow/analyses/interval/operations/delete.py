"""Delete operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.delete import Delete

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    is_signed_type,
    get_bit_width,
    type_to_sort,
    constant_to_term,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class DeleteHandler(BaseOperationHandler):
    """Handler for Solidity delete operations.

    In Solidity, `delete x` resets x to its type's default value:
    0 for integers, false for bool, zero-address for address, etc.
    All elementary types reset to the zero bit-pattern.
    """

    def handle(
        self,
        operation: Delete,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process delete by constraining lvalue to zero."""
        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        lvalue_name = get_variable_name(operation.lvalue)
        bit_width = get_bit_width(lvalue_type)
        signed = is_signed_type(lvalue_type)
        sort = type_to_sort(lvalue_type)

        tracked = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=signed, bit_width=bit_width
        )

        zero_term = constant_to_term(self.solver, 0, bit_width)
        self.solver.assert_constraint(tracked.term == zero_term)
        domain.state.set_variable(lvalue_name, tracked)
