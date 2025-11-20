"""Operation handler registry for interval analysis."""

from typing import Dict, Optional, Type, TYPE_CHECKING


from slither.analyses.data_flow.analyses.interval.operations.return_handler import ReturnHandler
from slither.analyses.data_flow.analyses.interval.operations.solidity_call import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.analyses.interval.operations.assignment import AssignmentHandler
from slither.analyses.data_flow.analyses.interval.operations.binary import BinaryHandler
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from .base import BaseOperationHandler
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain


class OperationHandlerRegistry:
    """Registry for mapping operation types to their handlers."""

    def __init__(self, solver: Optional["SMTSolver"] = None) -> None:
        """
        Initialize the registry with handlers.

        Args:
            solver: The SMT solver instance (optional)
        """
        self._solver = solver
        self._handlers: Dict[Type[Operation], "BaseOperationHandler"] = {}
        self._logger = get_logger()

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default operation handlers."""
        self.register(Assignment, AssignmentHandler)
        self.register(Binary, BinaryHandler)
        self.register(SolidityCall, SolidityCallHandler)
        self.register(Return, ReturnHandler)

    def register(
        self, operation_type: Type[Operation], handler_class: Type["BaseOperationHandler"]
    ) -> None:
        """
        Register a handler for an operation type.

        Args:
            operation_type: The operation type to handle
            handler_class: The handler class (will be instantiated with solver)
        """
        handler = handler_class(self._solver)
        self._handlers[operation_type] = handler

    def get_handler(self, operation: Operation) -> "BaseOperationHandler":
        """
        Get the handler for an operation.

        Args:
            operation: The operation to get a handler for

        Returns:
            The handler for the operation

        Raises:
            NotImplementedError: If no handler is registered for the operation type
        """
        operation_type = type(operation)
        handler = self._handlers.get(operation_type)
        if handler is None:
            operation_name = operation_type.__name__
            self._logger.error_and_raise(
                "No handler registered for operation type: {operation_name}",
                NotImplementedError,
                operation_name=operation_name,
            )
        return handler

    def has_handler(self, operation: Operation) -> bool:
        """
        Check if a handler exists for an operation.

        Args:
            operation: The operation to check

        Returns:
            True if a handler exists, False otherwise
        """
        return type(operation) in self._handlers
