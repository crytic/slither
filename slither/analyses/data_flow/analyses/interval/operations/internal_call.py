"""Internal call operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations.function import Function
from slither.slithir.operations.internal_call import InternalCall

if TYPE_CHECKING:
    from slither.slithir.operations.call import Call


class InternalCallHandler(InterproceduralHandler):
    """Handler for internal call operations.

    Performs interprocedural analysis by mapping call arguments to
    internal function parameters and analyzing the function body.
    """

    _call_counter: int = 0

    def _get_called_function(self, operation: "Call") -> Function | None:
        """Extract the called Function from the internal call."""
        if not isinstance(operation, InternalCall):
            return None
        func = operation.function
        if isinstance(func, Function):
            return func
        return None

    def _build_call_prefix(self, operation: "Call") -> str:
        """Build unique prefix for internal call."""
        InternalCallHandler._call_counter += 1
        func_name = operation.function.name if operation.function else "unknown"
        return f"_int{InternalCallHandler._call_counter}_{func_name}_"
