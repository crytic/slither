from typing import List

from slither.analyses.data_flow.interval.domain import IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.interval_calculator import IntervalCalculator
from slither.analyses.data_flow.interval.type_system import TypeSystem
from slither.analyses.data_flow.interval.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables.constant import Constant


class FunctionCallAnalyzer:
    """
    Handles inter-procedural analysis including internal function calls,
    argument-to-parameter mapping, and return value constraint propagation.
    """

    def __init__(self, type_system: TypeSystem, variable_manager: VariableManager):
        self.type_system = type_system
        self.variable_manager = variable_manager
        self._functions_seen: set[Function] = set()

    def handle_function_call(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: InternalCall,
        functions: List[Function],
        analysis_instance=None,
    ) -> None:
        """Handle internal function calls with inter-procedural constraint propagation."""
        called_function = operation.function

        if not isinstance(called_function, Function) or called_function in self._functions_seen:
            return

        # Mark function as being analyzed to prevent infinite recursion
        self._functions_seen.add(called_function)

        try:
            # Map caller arguments to callee parameters
            self._map_arguments_to_parameters(operation, domain, called_function)

            # Recursively analyze the called function using the same domain
            for function_node in called_function.nodes:
                for ir in function_node.irs:
                    # Analyze all operations in the called function
                    if isinstance(ir, (InternalCall, SolidityCall, Binary, Assignment, Return)):
                        if analysis_instance:
                            # Use the provided analysis instance to maintain context
                            analysis_instance.transfer_function_helper(
                                function_node, domain, ir, [called_function]
                            )

            # Apply return value constraints if the function has a return value
            if operation.lvalue:
                self._apply_return_constraints(operation, domain, called_function)

        finally:
            # Remove from analyzed set to allow re-analysis if needed
            self._functions_seen.discard(called_function)

    def _map_arguments_to_parameters(
        self, operation: InternalCall, domain: IntervalDomain, called_function: Function
    ) -> None:
        """Map caller arguments to callee parameters in the domain."""
        for arg, param in zip(operation.arguments, called_function.parameters):
            # Only process numeric parameters
            if not (
                isinstance(param.type, ElementaryType)
                and self.type_system.is_numeric_type(param.type)
            ):
                continue

            arg_name = self.variable_manager.get_canonical_name(arg)

            if arg_name in domain.state.info:
                # Copy existing interval from argument to parameter
                arg_interval = domain.state.info[arg_name]
                domain.state.info[param.canonical_name] = arg_interval.deep_copy()
            else:
                # Create default interval for parameter
                min_val, max_val = self.type_system.get_type_bounds(param.type)
                domain.state.info[param.canonical_name] = (
                    IntervalCalculator.create_interval_from_type(param.type, min_val, max_val)
                )

    # function caller() {
    #     uint256 result = foo();  // ← This triggers FunctionCallAnalyzer
    #     // result should get the constraints from foo's return value
    # }

    def _apply_return_constraints(
        self, operation: InternalCall, domain: IntervalDomain, called_function: Function
    ) -> None:
        """Apply return value constraints to the caller's domain."""
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
                        self._process_return_values(operation, domain, called_function, ir.values)
                        # Also propagate constraints back to caller arguments
                        self._process_argument_refinements(
                            operation, domain, called_function, ir.values
                        )
                        return

    def _process_return_values(
        self,
        operation: InternalCall,
        domain: IntervalDomain,
        called_function: Function,
        return_values: List[Variable],
    ) -> None:
        """Process return values (single or multiple) and apply constraints."""
        if not called_function.return_type or operation.lvalue is None:
            return

        # Handle single return value
        if len(return_values) == 1 and len(called_function.return_type) == 1:
            return_type = called_function.return_type[0]
            if isinstance(return_type, ElementaryType) and self.type_system.is_numeric_type(
                return_type
            ):
                return_value = return_values[0]
                result_var_name = self.variable_manager.get_canonical_name(operation.lvalue)

                if isinstance(return_value, Variable):
                    return_var_name = self.variable_manager.get_canonical_name(return_value)
                    # Look for the return value identifier created by OperationHandler
                    return_identifier = f"return_{return_var_name}"
                    if return_identifier in domain.state.info:
                        domain.state.info[result_var_name] = domain.state.info[
                            return_identifier
                        ].deep_copy()
                    elif return_var_name in domain.state.info:
                        # Fallback to original variable name
                        domain.state.info[result_var_name] = domain.state.info[
                            return_var_name
                        ].deep_copy()
                elif isinstance(return_value, Constant):
                    const_value = self.variable_manager.create_constant_interval(
                        return_value, operation.lvalue
                    )
                    domain.state.info[result_var_name] = const_value

        # Handle multiple return values (tuple)
        elif len(return_values) > 1 and len(called_function.return_type) > 1:
            # Check if lvalue is a TupleVariable
            if hasattr(operation.lvalue, "type") and isinstance(operation.lvalue.type, list):
                # For tuple assignments, we need to find the actual variable names
                # Look for unpack operations that assign tuple elements to named variables
                self._find_and_assign_tuple_elements(
                    operation, domain, return_values, called_function.return_type
                )

    def _find_and_assign_tuple_elements(
        self,
        operation: InternalCall,
        domain: IntervalDomain,
        return_values: List[Variable],
        return_types: List[Type],
    ) -> None:
        """Find unpack operations and assign constraints to the actual variable names."""
        # Look for unpack operations in the same node or subsequent nodes
        for node in operation.node.function.nodes:
            for ir in node.irs:
                if isinstance(ir, Unpack):
                    # This is an Unpack operation
                    if ir.tuple == operation.lvalue:
                        # This unpack operation is for our tuple
                        element_index = ir.index
                        if element_index < len(return_values):
                            return_value = return_values[element_index]
                            return_type = return_types[element_index]

                            if isinstance(
                                return_type, ElementaryType
                            ) and self.type_system.is_numeric_type(return_type):
                                if ir.lvalue is None:
                                    continue
                                element_var_name = self.variable_manager.get_canonical_name(
                                    ir.lvalue
                                )

                                if isinstance(return_value, Variable):
                                    return_var_name = self.variable_manager.get_canonical_name(
                                        return_value
                                    )
                                    # Look for the return value identifier created by OperationHandler
                                    return_identifier = f"return_{return_var_name}"
                                    if return_identifier in domain.state.info:
                                        domain.state.info[element_var_name] = domain.state.info[
                                            return_identifier
                                        ].deep_copy()
                                    elif return_var_name in domain.state.info:
                                        # Fallback to original variable name
                                        domain.state.info[element_var_name] = domain.state.info[
                                            return_var_name
                                        ].deep_copy()
                                elif isinstance(return_value, Constant):
                                    const_value = self.variable_manager.create_constant_interval(
                                        return_value, ir.lvalue
                                    )
                                    domain.state.info[element_var_name] = const_value

    def _process_argument_refinements(
        self,
        operation: InternalCall,
        domain: IntervalDomain,
        called_function: Function,
        return_values: List[Variable],
    ) -> None:
        """Propagate constraints from callee back to caller arguments."""
        # Map callee parameters to caller arguments
        for arg, param in zip(operation.arguments, called_function.parameters):
            if not (
                isinstance(param.type, ElementaryType)
                and self.type_system.is_numeric_type(param.type)
            ):
                continue

            arg_name = self.variable_manager.get_canonical_name(arg)
            param_name = param.canonical_name

            # If the parameter has constraints in the callee, propagate them back to the argument
            if param_name in domain.state.info:
                arg_interval = domain.state.info[param_name]
                if arg_name in domain.state.info:
                    # Merge constraints (intersection of intervals)
                    current_interval = domain.state.info[arg_name]
                    new_lower = max(current_interval.lower_bound, arg_interval.lower_bound)
                    new_upper = min(current_interval.upper_bound, arg_interval.upper_bound)

                    if new_lower <= new_upper:
                        domain.state.info[arg_name] = IntervalInfo(
                            lower_bound=new_lower,
                            upper_bound=new_upper,
                            var_type=current_interval.var_type,
                        )
                else:
                    # Create new interval for the argument
                    domain.state.info[arg_name] = arg_interval.deep_copy()
