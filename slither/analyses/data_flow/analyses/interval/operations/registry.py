"""Operation handler registry for interval analysis."""

from typing import Dict, Optional, Type, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.assignment import AssignmentHandler
from slither.analyses.data_flow.analyses.interval.operations.binary import BinaryHandler
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from .base import BaseOperationHandler
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


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

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default operation handlers."""
        self.register(Assignment, AssignmentHandler)
        self.register(Binary, BinaryHandler)

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

    def get_handler(self, operation: Operation) -> Optional["BaseOperationHandler"]:
        """
        Get the handler for an operation.

        Args:
            operation: The operation to get a handler for

        Returns:
            The handler for the operation, or None if no handler is registered
        """
        operation_type = type(operation)
        return self._handlers.get(operation_type)

    def has_handler(self, operation: Operation) -> bool:
        """
        Check if a handler exists for an operation.

        Args:
            operation: The operation to check

        Returns:
            True if a handler exists, False otherwise
        """
        return type(operation) in self._handlers
