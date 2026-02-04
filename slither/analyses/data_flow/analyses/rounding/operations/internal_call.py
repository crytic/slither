"""Internal call operation handler for rounding analysis."""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.internal_call import InternalCall


class InternalCallHandler(InterproceduralHandler):
    """Handler for internal call operations.

    Performs interprocedural analysis by inferring rounding from function name
    or analyzing the function body.
    """

    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function from the internal call."""
        if not isinstance(operation, InternalCall):
            return None
        called_function = operation.function
        if isinstance(called_function, Function):
            return called_function
        return None

    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""
        if not isinstance(operation, InternalCall):
            return ""
        if operation.function:
            return operation.function.name
        return str(operation.function_name)
