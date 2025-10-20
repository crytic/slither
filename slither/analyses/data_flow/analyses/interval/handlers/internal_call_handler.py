import decimal
from decimal import Decimal
from typing import TYPE_CHECKING, List, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.index import Index
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis


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

        logger.info(f"Handling internal call to function: {callee_function.name}")

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

            #            logger.debug(f"Processing internal call to function: {callee_function.name}")

            # Process all operations in the called function
            for callee_function_node in callee_function.nodes:
                # Initialize domain from bottom for the first node of the called function
                # This ensures state variables are available in the callee's context
                if callee_function_node == callee_function.nodes[0]:
                    analysis_instance._initialize_domain_from_bottom(callee_function_node, domain)

                for ir_operation in callee_function_node.irs:
                    # if not isinstance(
                    #     ir_operation, Union[InternalCall, SolidityCall, Binary, Assignment, Return, HighLevelCall, Index]
                    # ):
                    #     continue

                    analysis_instance.transfer_function_helper(
                        callee_function_node, domain, ir_operation
                    )

            # Copy callee parameter constraints back to caller arguments
            self.constraint_manager.copy_callee_parameter_constraints_back_to_caller_arguments(
                internal_call_operation.arguments, callee_function.parameters, domain
            )

            # Apply return value constraints if the function has a return value
            self._apply_return_value_constraints(internal_call_operation, domain, callee_function)

        finally:
            self.unmark_function_seen(callee_function)

    def _apply_return_value_constraints(
        self, operation: InternalCall, domain: IntervalDomain, called_function: Function
    ) -> None:
        """Apply return value constraints using constraint manager."""
        # Early return if no return value expected
        if not operation.lvalue:
            return

        # Early return if function has no return type
        if not called_function.return_type or len(called_function.return_type) == 0:
            return

        # For assembly functions, look for assignments to return variables
        return_variables = called_function.returns
        if return_variables:
            # Create temporary variable for the return value
            self._create_return_temporary_variables(operation.lvalue, return_variables, domain)

            # Copy callee return constraints to caller variable
            self.constraint_manager.copy_callee_return_constraints_to_caller_variable(
                operation.lvalue, return_variables, called_function.return_type, domain
            )
        else:
            # Look for return statements and extract constraints
            for node in called_function.nodes:
                for ir in node.irs:
                    # Skip non-return operations
                    if not isinstance(ir, Return):
                        continue

                    # Skip return statements without values
                    if not ir.values:
                        continue

                    # Skip if return value count doesn't match expected count
                    if len(ir.values) != len(called_function.return_type):
                        continue

                    # Create temporary variable for the return value if it's a constant
                    self._create_return_temporary_variables(operation.lvalue, ir.values, domain)

                    # Copy callee return constraints to caller variable and exit
                    self.constraint_manager.copy_callee_return_constraints_to_caller_variable(
                        operation.lvalue, ir.values, called_function.return_type, domain
                    )

    def _create_return_temporary_variables(
        self, caller_lvalue: Variable, return_values: List[Variable], domain: IntervalDomain
    ) -> None:
        """Create temporary variables for return values."""
        if not caller_lvalue:
            return

        caller_lvalue_name = self.constraint_manager.variable_manager.get_variable_name(
            caller_lvalue
        )

        # Check if the caller lvalue is a temporary variable (like TMP_0)
        if isinstance(caller_lvalue, TemporaryVariable):
            # Process each return value
            for i, return_value in enumerate(return_values):
                var_type = self.constraint_manager.variable_manager.get_variable_type(return_value)

                if isinstance(return_value, Constant):
                    # Handle constant return values
                    if self.constraint_manager.variable_manager.is_type_numeric(var_type):
                        # Only convert to Decimal if it's a numeric type
                        try:
                            value = Decimal(str(return_value.value))
                            range_variable = RangeVariable(
                                interval_ranges=None,
                                valid_values=ValueSet([value]),
                                invalid_values=None,
                                var_type=var_type,
                            )
                        except (decimal.InvalidOperation, ValueError, TypeError):
                            # Skip non-numeric values that can't be converted to Decimal
                            range_variable = self._create_placeholder_for_type(var_type)
                    else:
                        # Create placeholder for non-numeric constants
                        range_variable = self._create_placeholder_for_type(var_type)
                else:
                    # Handle non-constant return values (variables, function calls, etc.)
                    range_variable = self._create_placeholder_for_type(var_type)

                # Store the temporary variable in domain state
                domain.state.set_range_variable(caller_lvalue_name, range_variable)
                logger.debug(f"Created temporary variable {caller_lvalue_name} for return value")
                break  # Only process the first return value for now

    def _create_placeholder_for_type(self, var_type) -> RangeVariable:
        """Create a placeholder range variable for a given type."""
        return RangeVariable(
            interval_ranges=[],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=var_type,
        )
