"""Assignment operation handler for rounding analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class AssignmentHandler(BaseOperationHandler):
    """Handler for assignment operations.

    Propagates rounding tag from right side to left side.
    """

    def handle(
        self,
        operation: Assignment,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process assignment operation."""
        if not operation.lvalue:
            return

        right_value = operation.rvalue
        if isinstance(right_value, Variable):
            tag = get_variable_tag(right_value, domain)
            domain.state.set_tag(operation.lvalue, tag, operation)
            self.analysis._check_annotation_for_variable(
                operation.lvalue, tag, operation, node, domain
            )
        # For non-variable rvalues (functions, tuples), leave as UNKNOWN
