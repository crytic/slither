"""Operation handler registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations import Assignment, Operation
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.phi import Phi
from slither.slithir.operations.phi_callback import PhiCallback
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.operations.unary import Unary

from slither.analyses.data_flow.analyses.interval.operations.assignment import (
    AssignmentHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.binary import (
    BinaryHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.high_level_call import (
    HighLevelCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.internal_call import (
    InternalCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.library_call import (
    LibraryCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.phi import (
    PhiHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.phi_callback import (
    PhiCallbackHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.return_operation import (
    ReturnHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
    TypeConversionHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.unary import (
    UnaryHandler,
)
from slither.analyses.data_flow.logger import get_logger

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver

logger = get_logger()


class OperationHandlerRegistry:
    """Maps operation types to handlers."""

    def __init__(self, solver: "SMTSolver"):
        self._solver = solver
        self._handlers: dict[type[Operation], BaseOperationHandler] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all implemented operation handlers."""
        self._handlers[Assignment] = AssignmentHandler(self._solver)
        self._handlers[Binary] = BinaryHandler(self._solver)
        self._handlers[HighLevelCall] = HighLevelCallHandler(self._solver)
        self._handlers[InternalCall] = InternalCallHandler(self._solver)
        self._handlers[LibraryCall] = LibraryCallHandler(self._solver)
        self._handlers[Phi] = PhiHandler(self._solver)
        self._handlers[PhiCallback] = PhiCallbackHandler(self._solver)
        self._handlers[Return] = ReturnHandler(self._solver)
        self._handlers[SolidityCall] = SolidityCallHandler(self._solver)
        self._handlers[TypeConversion] = TypeConversionHandler(self._solver)
        self._handlers[Unary] = UnaryHandler(self._solver)

    def get_handler(self, op_type: type[Operation]) -> BaseOperationHandler:
        """Get handler for operation type."""
        if op_type not in self._handlers:
            implemented = [handler.__name__ for handler in self._handlers.keys()]
            logger.error_and_raise(
                f"Operation '{op_type.__name__}' is not implemented. "
                f"Implemented: {implemented}",
                NotImplementedError,
            )
        return self._handlers[op_type]
