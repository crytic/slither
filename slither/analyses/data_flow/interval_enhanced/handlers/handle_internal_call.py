from typing import List, Union, TYPE_CHECKING

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.core.variables.variable import Variable
from slither.slithir.variables.constant import Constant
from decimal import Decimal

from loguru import logger

if TYPE_CHECKING:
    from slither.analyses.data_flow.interval_enhanced.analysis.analysis import (
        IntervalAnalysisEnhanced,
    )


class InternalCallHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self._functions_seen: set[Function] = set()
        self.variable_manager = VariableManager()
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
        operation: InternalCall,
        analysis_instance: "IntervalAnalysisEnhanced",
    ) -> None:
        """Handle internal calls in the contract"""
        called_function = operation.function

        if called_function is None:
            logger.error(f"Internal call has no function: {operation}")
            raise ValueError(f"Internal call has no function: {operation}")

        if self.is_function_seen(called_function):
            return

        # Mark function as being analyzed to prevent infinite recursion
        self.mark_function_seen(called_function)

        try:
            # Propagate constraints from caller arguments to callee parameters
            self.constraint_manager.propagate_constraints_from_caller_to_callee(
                operation.arguments, called_function.parameters, domain
            )

            for function_node in called_function.nodes:
                for ir in function_node.irs:
                    if not isinstance(
                        ir, Union[InternalCall, SolidityCall, Binary, Assignment, Return]
                    ):
                        continue

                    analysis_instance.transfer_function_helper(
                        function_node, domain, ir, [called_function]
                    )

            # Propagate constraints back to caller arguments using constraint manager
            self.constraint_manager.propagate_constraints_from_callee_to_caller(
                operation.arguments, called_function.parameters, domain
            )

            # Apply return value constraints if the function has a return value
            if operation.lvalue:
                self._apply_return_value_constraints(operation, domain, called_function)

        finally:
            self.unmark_function_seen(called_function)

    def _apply_return_value_constraints(
        self, operation: InternalCall, domain: IntervalDomain, called_function: Function
    ) -> None:
        """Apply return value constraints using constraint manager."""
        if not operation.lvalue:
            return

        if not called_function.return_type or len(called_function.return_type) == 0:
            return

        # Look for return statements and extract constraints
        for node in called_function.nodes:
            for ir in node.irs:
                if isinstance(ir, Return) and ir.values:
                    # Handle both single and multiple return values
                    if len(ir.values) == len(called_function.return_type):
                        self.constraint_manager.apply_return_value_constraints(
                            operation.lvalue, ir.values, called_function.return_type, domain
                        )
                        return
