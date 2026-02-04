"""Library call operation handler for rounding analysis."""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.library_call import LibraryCall


class LibraryCallHandler(InterproceduralHandler):
    """Handler for library call operations.

    Library functions are compiled with the contract, so we have access
    to the function body for interprocedural analysis.
    """

    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function from the library call."""
        if not isinstance(operation, LibraryCall):
            return None
        called_function = operation.function
        if isinstance(called_function, Function):
            return called_function
        return None

    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""
        if not isinstance(operation, LibraryCall):
            return ""
        return str(operation.function_name.value)
