"""Main binary operation handler that dispatches to specific handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.addition import (
    AdditionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.division import (
    DivisionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary import (
    multiplication,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.subtraction import (
    SubtractionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary, BinaryType

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class BinaryHandler(BaseOperationHandler):
    """Handler for binary operations - dispatches to type-specific handlers."""

    def __init__(self, analysis: "RoundingAnalysis") -> None:
        super().__init__(analysis)
        self._handlers: dict[BinaryType, BinaryOperationHandler] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register handlers for each binary operation type."""
        self._handlers[BinaryType.DIVISION] = DivisionHandler(self._analysis)
        self._handlers[BinaryType.SUBTRACTION] = SubtractionHandler(self._analysis)
        self._handlers[BinaryType.ADDITION] = AdditionHandler(self._analysis)
        multiplication_handler = multiplication.MultiplicationHandler(self._analysis)
        self._handlers[BinaryType.MULTIPLICATION] = multiplication_handler

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process binary operation by dispatching to appropriate handler."""
        if not operation.lvalue:
            return

        left_tag = get_variable_tag(operation.variable_left, domain)
        right_tag = get_variable_tag(operation.variable_right, domain)
        operation_type = operation.type

        handler = self._handlers.get(operation_type)
        if handler is not None:
            handler.handle(operation, domain, node, left_tag, right_tag)
        elif operation_type == BinaryType.POWER:
            self.analysis._logger.warning("Rounding for POWER is not implemented yet")


# Import here to avoid circular import at module level
if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )
