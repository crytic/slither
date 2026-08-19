"""Operation handler registry for rounding analysis."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.operations.assignment import (
    AssignmentHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.handler import (
    BinaryHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.return_operation import (
    ReturnHandler,
)
from slither.slithir.operations import Assignment, Operation
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.return_operation import Return

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )

logger = logging.getLogger("DataFlow")


class OperationHandlerRegistry:
    """Maps operation types to handlers for rounding analysis."""

    def __init__(self, analysis: RoundingAnalysis):
        self._analysis = analysis
        self._handlers: dict[type[Operation], BaseOperationHandler] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all implemented operation handlers."""
        self._handlers[Binary] = BinaryHandler(self._analysis)
        self._handlers[Assignment] = AssignmentHandler(self._analysis)
        interprocedural = InterproceduralHandler(self._analysis)
        self._handlers[InternalCall] = interprocedural
        self._handlers[HighLevelCall] = interprocedural
        self._handlers[LibraryCall] = interprocedural
        self._handlers[Return] = ReturnHandler(self._analysis)

    def get_handler(self, operation_type: type[Operation]) -> BaseOperationHandler | None:
        """Get handler for operation type, or None if not registered."""
        return self._handlers.get(operation_type)

    def has_handler(self, operation_type: type[Operation]) -> bool:
        """Check if a handler is registered for the operation type."""
        return operation_type in self._handlers
