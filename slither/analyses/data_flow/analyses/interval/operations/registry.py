"""Operation handler registry for interval analysis."""

from typing import Any, Dict, Optional, Type, TYPE_CHECKING


from slither.analyses.data_flow.analyses.interval.operations.internal_call import (
    InternalCallHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.phi import PhiHandler
from slither.analyses.data_flow.analyses.interval.operations.return_handler import ReturnHandler
from slither.analyses.data_flow.analyses.interval.operations.solidity_call import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.analyses.interval.operations.assignment import AssignmentHandler
from slither.analyses.data_flow.analyses.interval.operations.binary import BinaryHandler
from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
    TypeConversionHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.new_elementary_type import (
    NewElementaryTypeHandler,
)
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.phi import Phi
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.operations.new_elementary_type import NewElementaryType
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from .base import BaseOperationHandler
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
    from slither.core.cfg.node import Node


class OperationHandlerRegistry:
    """Registry for mapping operation types to their handlers."""

    def __init__(
        self,
        solver: Optional["SMTSolver"] = None,
        analysis: Optional["IntervalAnalysis"] = None,
    ) -> None:
        """
        Initialize the registry with handlers.

        Args:
            solver: The SMT solver instance (optional)
            analysis: The interval analysis instance (optional, needed for interprocedural analysis)
        """
        self._solver = solver
        self._analysis = analysis
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
        self.register(InternalCall, InternalCallHandler)
        self.register(Phi, PhiHandler)
        self.register(TypeConversion, TypeConversionHandler)
        self.register(NewElementaryType, NewElementaryTypeHandler)

    def register(
        self, operation_type: Type[Operation], handler_class: Type["BaseOperationHandler"]
    ) -> None:
        """
        Register a handler for an operation type.

        Args:
            operation_type: The operation type to handle
            handler_class: The handler class (will be instantiated with solver and analysis)
        """
        handler = handler_class(self._solver, self._analysis)
        self._handlers[operation_type] = handler

    @property
    def analysis(self) -> Optional["IntervalAnalysis"]:
        """Get the interval analysis instance."""
        return self._analysis

    def get_handler(
        self, operation: Operation, node: Optional["Node"] = None, domain: Optional[Any] = None
    ) -> "BaseOperationHandler":
        """
        Get the handler for an operation.

        Args:
            operation: The operation to get a handler for
            node: Optional node context (for debugging)
            domain: Optional domain context (for debugging)

        Returns:
            The handler for the operation

        Raises:
            NotImplementedError: If no handler is registered for the operation type
        """
        operation_type = type(operation)
        handler = self._handlers.get(operation_type)
        if handler is None:
            operation_name = operation_type.__name__
            # Pass context for debugging in embed session
            context = {"operation": operation, "operation_name": operation_name}
            if node is not None:
                context["node"] = node
            if domain is not None:
                context["domain"] = domain
            self._logger.error_and_raise(
                "No handler registered for operation type: {operation_name}",
                NotImplementedError,
                embed_on_error=True,
                **context,
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
