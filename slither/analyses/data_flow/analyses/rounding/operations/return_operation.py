"""Return operation handler for rounding analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.return_operation import Return

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class ReturnHandler(BaseOperationHandler):
    """Handler for return operations - checks annotations on return variables."""

    def handle(
        self,
        operation: Return,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process return operation - validates any annotated return variables."""
        for return_value in operation.values:
            if not isinstance(return_value, Variable):
                continue
            return_tag = domain.state.get_tag(return_value)
            self.analysis._check_annotation_for_variable(
                return_value, return_tag, operation, node, domain
            )
