from typing import Union, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall

from loguru import logger

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import (
        IntervalAnalysis,
    )


class InternalCallHandler:
    def __init__(self, constraint_manager: ConstraintManager = None):
        self._functions_seen: set[Function] = set()
        self.constraint_manager = constraint_manager or ConstraintManager()

    def mark_function_seen(self, function: Function) -> bool:
        """Mark a function as seen/analyzed."""
        if function in self._functions_seen:
            return False
        self._functions_seen.add(function)
        return True

    def unmark_function_seen(self, function: Function) -> bool:
        """Unmark a function as seen/analyzed."""
        if function in self._functions_seen:
            self._functions_seen.remove(function)
            return True
        return False

    def is_function_seen(self, function: Function) -> bool:
        """Check if a function has been seen/analyzed."""
        return function in self._functions_seen

    def handle_internal_call(
        self,
        node: Node,
        domain: IntervalDomain,
        internal_call_operation: InternalCall,
        analysis_instance: "IntervalAnalysis",
    ) -> None:
        """Handle internal function calls with constraint propagation for interprocedural analysis."""
        callee_function = internal_call_operation.function

        if callee_function is None:
            logger.error(f"Internal call has no function: {internal_call_operation}")
            raise ValueError(f"Internal call has no function: {internal_call_operation}")

        if self.is_function_seen(callee_function):
            return

        # Mark function as being analyzed to prevent infinite recursion
        self.mark_function_seen(callee_function)

        try:
            # Copy constraints from caller arguments to callee parameters
            self.constraint_manager.copy_caller_constraints_to_callee_parameters(
                internal_call_operation.arguments, callee_function.parameters, domain
            )

            logger.debug(f"Processing internal call to function: {callee_function.name}")

            # Process all operations in the called function
            for callee_function_node in callee_function.nodes:
                for ir_operation in callee_function_node.irs:
                    if not isinstance(
                        ir_operation, Union[InternalCall, SolidityCall, Binary, Assignment, Return]
                    ):
                        continue

                    analysis_instance.transfer_function_helper(
                        callee_function_node, domain, ir_operation
                    )

            # TODO: Propagate constraints back from callee to caller arguments
            # This would require implementing propagate_constraints_from_callee_to_caller in ConstraintManager

            # TODO: Apply return value constraints if the function has a return value

        finally:
            self.unmark_function_seen(callee_function)
