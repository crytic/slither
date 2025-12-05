from typing import List, Optional, Set

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.variables.constant import Constant


class InternalCallHandler(BaseOperationHandler):
    """Handler for internal function calls with interprocedural analysis.

    This handler recursively analyzes called functions, propagating state constraints
    through parameters and merging results back into the caller's state.
    """

    # Class-level call stack to track recursion across all handler instances
    _call_stack: Set[Function] = set()

    def handle(self, operation: InternalCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling internal call: {operation}", operation=operation)

        if self.solver is None:
            self.logger.warning("Solver is None, skipping internal call")
            return

        if self.analysis is None:
            self.logger.warning("Analysis instance is None, skipping interprocedural analysis")
            return

        # Skip if domain is not in STATE variant
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping internal call")
            return

        function = operation.function
        if not isinstance(function, Function):
            self.logger.debug("Internal call function is not a Function instance, skipping")
            return

        # Cycle detection: check if function is already in call stack
        if function in InternalCallHandler._call_stack:
            self.logger.debug(
                "Recursion detected for function '{name}', skipping interprocedural analysis",
                name=function.name,
            )
            # Fallback to simple return value tracking
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, domain)
            return

        # Check if function has nodes (is implemented)
        if not function.nodes:
            self.logger.debug(
                "Function '{name}' has no nodes (not implemented), skipping",
                name=function.name,
            )
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, domain)
            return

        # Add function to call stack
        InternalCallHandler._call_stack.add(function)

        try:
            # Perform interprocedural analysis
            self._analyze_called_function(operation, domain, function)
        finally:
            # Remove function from call stack
            InternalCallHandler._call_stack.discard(function)

    def _analyze_called_function(
        self, operation: InternalCall, caller_domain: IntervalDomain, called_function: Function
    ) -> None:
        """Recursively analyze the called function with propagated state."""
        self.logger.debug(
            "Analyzing called function '{name}' interprocedurally",
            name=called_function.name,
        )

        # 1. Create a copy of the caller's domain state
        callee_domain = IntervalDomain.with_state(caller_domain.state.deep_copy())

        # 2. Constrain function parameters based on actual arguments
        self._constrain_parameters(operation, caller_domain, callee_domain, called_function)

        # 3. Run analysis on the called function
        engine = Engine.new(analysis=self.analysis, function=called_function)

        # Initialize entry point with the constrained domain
        entry_point = called_function.entry_point
        if entry_point is not None:
            # Override the initial state at entry point with our constrained domain
            engine.state[entry_point.node_id] = AnalysisState(
                pre=callee_domain.deep_copy(), post=callee_domain.deep_copy()
            )

        # Run the analysis
        engine.run_analysis()

        # 4. Re-constrain parameters after analysis to ensure SSA versions are constrained
        # This is needed because the analysis may create new SSA versions (like x_1) that
        # weren't present when we initially constrained the parameters
        self._reconstrain_parameters_after_analysis(
            operation, caller_domain, callee_domain, called_function, engine
        )

        # 5. Get the final state from the function's exit points
        final_domain = self._get_final_domain(called_function, engine)

        # 6. Merge results back into caller's domain
        self._merge_callee_state_into_caller(caller_domain, final_domain)

        # 7. Extract and assign return value constraints
        if operation.lvalue is not None:
            self._extract_return_value(operation, final_domain, caller_domain)

    def _constrain_parameters(
        self,
        operation: InternalCall,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
    ) -> None:
        """Constrain function parameters in callee domain based on caller arguments."""
        if not operation.arguments or not called_function.parameters:
            return

        # Match arguments to parameters (assuming positional matching)
        for i, param in enumerate(called_function.parameters):
            if i >= len(operation.arguments):
                break

            arg = operation.arguments[i]
            param_name = IntervalSMTUtils.resolve_variable_name(param)
            if param_name is None:
                continue

            param_type = IntervalSMTUtils.resolve_elementary_type(param.type)
            if param_type is None:
                continue

            # Get or create parameter variable in callee domain
            param_tracked = IntervalSMTUtils.get_tracked_variable(callee_domain, param_name)
            if param_tracked is None:
                param_tracked = IntervalSMTUtils.create_tracked_variable(
                    self.solver, param_name, param_type
                )
                if param_tracked is None:
                    continue
                callee_domain.state.set_range_variable(param_name, param_tracked)
                param_tracked.assert_no_overflow(self.solver)

            # Handle argument: constant or variable
            if isinstance(arg, Constant):
                # Argument is a constant - constrain parameter to the constant value
                const_value = arg.value
                self._constrain_parameter_to_constant(
                    param_name=param_name,
                    param_tracked=param_tracked,
                    const_value=const_value,
                    param_type=param_type,
                    callee_domain=callee_domain,
                )
                continue

            # Argument is a variable - get its tracked variable from caller domain
            arg_name = IntervalSMTUtils.resolve_variable_name(arg)
            if arg_name is None:
                continue

            arg_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, arg_name)
            if arg_tracked is None:
                if hasattr(arg, "value"):
                    const_value = arg.value
                    self._constrain_parameter_to_constant(
                        param_name=param_name,
                        param_tracked=param_tracked,
                        const_value=const_value,
                        param_type=param_type,
                        callee_domain=callee_domain,
                    )
                continue

            # Constrain parameter to equal argument value
            constraint: SMTTerm = param_tracked.term == arg_tracked.term
            self.solver.assert_constraint(constraint)
            self.logger.debug(
                "Constrained parameter '{param}' to equal argument '{arg}'",
                param=param_name,
                arg=arg_name,
            )

            self._constrain_parameter_ssa_versions(
                base_name=param_name,
                rhs_term=arg_tracked.term,
                param_type=param_type,
                callee_domain=callee_domain,
            )

    def _reconstrain_parameters_after_analysis(
        self,
        operation: InternalCall,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
        engine: Engine,
    ) -> None:
        """Re-constrain parameters after analysis to ensure all SSA versions are constrained."""
        if not operation.arguments or not called_function.parameters:
            return

        # Get all domain states from all nodes to ensure we constrain across the entire function
        all_domains: List[IntervalDomain] = []
        for node in called_function.nodes:
            node_state = engine.state.get(node.node_id)
            if node_state and node_state.post.variant == DomainVariant.STATE:
                all_domains.append(node_state.post)

        if not all_domains:
            return

        # Match arguments to parameters
        for i, param in enumerate(called_function.parameters):
            if i >= len(operation.arguments):
                break

            arg = operation.arguments[i]
            param_name = IntervalSMTUtils.resolve_variable_name(param)
            if param_name is None:
                continue

            param_type = IntervalSMTUtils.resolve_elementary_type(param.type)
            if param_type is None:
                continue

            # Get the constraint value (constant or variable term)
            rhs_term: Optional[SMTTerm] = None
            if isinstance(arg, Constant):
                const_value = arg.value
                # Get sort from any tracked variable with this base name
                for domain in all_domains:
                    param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
                    if param_tracked is not None:
                        rhs_term = self.solver.create_constant(const_value, param_tracked.sort)
                        break
                if rhs_term is None:
                    # Create a tracked variable just to get the sort
                    temp_tracked = IntervalSMTUtils.create_tracked_variable(
                        self.solver, param_name, param_type
                    )
                    if temp_tracked is not None:
                        rhs_term = self.solver.create_constant(const_value, temp_tracked.sort)
            else:
                arg_name = IntervalSMTUtils.resolve_variable_name(arg)
                if arg_name is None:
                    continue
                arg_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, arg_name)
                if arg_tracked is None:
                    continue
                rhs_term = arg_tracked.term

            if rhs_term is None:
                continue

            # Constrain the base parameter and first SSA version (_1) in ALL analyzed domains
            # This ensures the constraint propagates through the entire function
            # Note: We only constrain _1 (the parameter), not later versions (_2, _3, etc.)
            # which are results of assignments
            for domain in all_domains:
                # First, constrain the base parameter itself
                param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
                if param_tracked is not None:
                    constraint: SMTTerm = param_tracked.term == rhs_term
                    self.solver.assert_constraint(constraint)
                    self.logger.debug(
                        "Re-constrained base parameter '{param}' to match argument/constant",
                        param=param_name,
                    )

                # Then constrain only the first SSA version (_1) which represents the parameter
                self._constrain_parameter_ssa_versions(
                    base_name=param_name,
                    rhs_term=rhs_term,
                    param_type=param_type,
                    callee_domain=domain,
                )

    def _get_final_domain(self, function: Function, engine: Engine) -> Optional[IntervalDomain]:
        """Get the final domain state from function exit points (return statements)."""
        # Find return nodes (nodes with no successors or explicit return operations)
        return_nodes = [node for node in function.nodes if not node.sons]

        if not return_nodes:
            # If no explicit return nodes, use the last node
            if function.nodes:
                return_nodes = [function.nodes[-1]]
            else:
                return None

        # Merge all return node states
        final_domains = []
        for return_node in return_nodes:
            node_state = engine.state.get(return_node.node_id)
            if node_state and node_state.post.variant == DomainVariant.STATE:
                final_domains.append(node_state.post)

        if not final_domains:
            return None

        # Merge all return paths (assuming single return for now)
        if len(final_domains) == 1:
            return final_domains[0]

        # Multiple return paths - merge them
        merged = final_domains[0].deep_copy()
        for other in final_domains[1:]:
            merged.join(other)
        return merged

    def _merge_callee_state_into_caller(
        self, caller_domain: IntervalDomain, callee_domain: Optional[IntervalDomain]
    ) -> None:
        """Merge callee's state modifications back into caller's domain."""
        if callee_domain is None or callee_domain.variant != DomainVariant.STATE:
            return

        # Merge all state variables that were modified in the callee
        # (For now, merge all variables - in a more sophisticated implementation,
        # we'd track which variables were actually modified)
        for var_name, callee_tracked in callee_domain.state.get_range_variables().items():
            # Skip parameter variables (they're local to the callee)
            if self._is_parameter_variable(var_name, callee_domain):
                continue

            caller_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, var_name)
            if caller_tracked is not None:
                # Variable exists in caller - merge constraints
                # For now, we'll update the caller's variable with callee's constraints
                # This is a simplification - a full implementation would merge intervals
                constraint: SMTTerm = caller_tracked.term == callee_tracked.term
                self.solver.assert_constraint(constraint)
                self.logger.debug(
                    "Merged state variable '{name}' from callee to caller", name=var_name
                )
            else:
                # New variable created in callee - add to caller
                caller_domain.state.set_range_variable(var_name, callee_tracked)
                self.logger.debug(
                    "Added new state variable '{name}' from callee to caller", name=var_name
                )

        # Merge binary operations
        for var_name, callee_op in callee_domain.state.get_binary_operations().items():
            if not caller_domain.state.has_binary_operation(var_name):
                caller_domain.state.set_binary_operation(var_name, callee_op)

    def _extract_return_value(
        self,
        operation: InternalCall,
        callee_domain: IntervalDomain,
        caller_domain: IntervalDomain,
    ) -> None:
        """Extract return value constraints from callee and assign to lvalue."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Find return operations in the called function
        called_function = operation.function
        return_values = []
        for node in called_function.nodes:
            for ir in node.irs:
                from slither.slithir.operations.return_operation import Return

                if isinstance(ir, Return) and ir.values:
                    return_values.extend(ir.values)

        if not return_values:
            self.logger.debug(
                "No return values found in callee function, using fallback",
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        # For now, assume single return value (as per requirement)
        return_value = return_values[0]
        return_value_base = getattr(return_value, "canonical_name", None) or getattr(
            return_value, "name", None
        )

        if return_value_base is None:
            self.logger.debug("Return value has no identifiable name, using fallback")
            self._handle_return_value_fallback(operation, caller_domain)
            return

        # Gather all candidate variables that match the return value base
        candidates: List[tuple[int, str, TrackedSMTVariable]] = []
        for var_name, tracked_var in callee_domain.state.get_range_variables().items():
            if var_name == return_value_base:
                candidates.append((-1, var_name, tracked_var))
            elif var_name.startswith(f"{return_value_base}|"):
                ssa_suffix = var_name.split("|", 1)[1]
                ssa_index = self._extract_ssa_index(ssa_suffix)
                candidates.append((ssa_index, var_name, tracked_var))

        if not candidates:
            self.logger.debug(
                "Return value base '{base}' not present in callee domain, using fallback",
                base=return_value_base,
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        # Select the candidate with the highest SSA index (latest version)
        candidates.sort(key=lambda item: item[0])
        return_value_index, return_value_name, return_value_tracked = candidates[-1]
        self.logger.debug(
            "Selected return value candidate '{name}' (ssa_index={index})",
            name=return_value_name,
            index=return_value_index,
        )

        # Get or create lvalue tracked variable in caller domain
        return_type: Optional[ElementaryType] = None
        if hasattr(operation, "variable_return_type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(operation.variable_return_type)
        if return_type is None and isinstance(called_function, Function):
            if called_function.return_type:
                return_type = IntervalSMTUtils.resolve_elementary_type(called_function.return_type)

        if return_type is None:
            # Try to infer from return value
            return_type = IntervalSMTUtils.resolve_elementary_type(
                return_value.type if hasattr(return_value, "type") else None
            )

        if return_type is None:
            self.logger.debug(
                "Could not determine return type for '{name}', using fallback",
                name=lvalue_name,
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, lvalue_name)
        if lvalue_tracked is None:
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if lvalue_tracked is None:
                self._handle_return_value_fallback(operation, caller_domain)
                return
            caller_domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        # Constrain lvalue to equal return value
        constraint: SMTTerm = lvalue_tracked.term == return_value_tracked.term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Extracted return value '{name}' from callee analysis, constrained to '{return_name}'",
            name=lvalue_name,
            return_name=return_value_name,
        )

    def _is_parameter_variable(self, var_name: str, domain: IntervalDomain) -> bool:
        """Check if a variable name corresponds to a function parameter."""
        # This is a heuristic - parameters are typically base variables without SSA versions
        # in the function's initial state
        # A more robust implementation would track parameter names explicitly
        return "|" not in var_name or var_name.endswith("_0")

    def _handle_return_value_fallback(
        self, operation: InternalCall, domain: IntervalDomain
    ) -> None:
        """Fallback: create tracked variable for return value without constraints."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        existing_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if existing_tracked is not None:
            return

        return_type: Optional[ElementaryType] = None
        if hasattr(operation, "variable_return_type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(operation.variable_return_type)
        if return_type is None:
            lvalue_type_attr = lvalue.type if hasattr(lvalue, "type") else None
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue_type_attr)
        if return_type is None and isinstance(operation.function, Function):
            function = operation.function
            if function.return_type:
                return_type = IntervalSMTUtils.resolve_elementary_type(function.return_type)

        if return_type is None:
            return

        tracked = IntervalSMTUtils.create_tracked_variable(self.solver, lvalue_name, return_type)
        if tracked is None:
            return

        domain.state.set_range_variable(lvalue_name, tracked)
        tracked.assert_no_overflow(self.solver)

    def _constrain_parameter_to_constant(
        self,
        param_name: str,
        param_tracked: TrackedSMTVariable,
        const_value: int,
        param_type: ElementaryType,
        callee_domain: IntervalDomain,
    ) -> None:
        """Constrain a parameter (and its initial SSA version) to a constant value."""
        const_term: SMTTerm = self.solver.create_constant(const_value, param_tracked.sort)
        constraint: SMTTerm = param_tracked.term == const_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained parameter '{param}' to constant value {value}",
            param=param_name,
            value=const_value,
        )

        self._constrain_parameter_ssa_versions(
            base_name=param_name,
            rhs_term=const_term,
            param_type=param_type,
            callee_domain=callee_domain,
        )

    def _constrain_parameter_ssa_versions(
        self,
        base_name: str,
        rhs_term: SMTTerm,
        param_type: ElementaryType,
        callee_domain: IntervalDomain,
    ) -> None:
        """Ensure the first SSA version (_1) for a parameter equals the provided term.

        Only constrain the first SSA version (_1) which represents the parameter value.
        Subsequent SSA versions (_2, _3, etc.) are results of assignments and should not
        be constrained to the parameter value.
        """
        # Extract base variable name (e.g., "x" from "SimpleFunction.double(uint8).x")
        base_var_name = (
            base_name.split(".")[-1]
            if "." in base_name
            else base_name.split("|")[-1] if "|" in base_name else base_name
        )

        # Create and constrain ONLY the first SSA version (_1) that represents the parameter
        # This is the version that appears first in the function body (e.g., x|x_1)
        first_ssa_name = f"{base_name}|{base_var_name}_1"

        # Check if it already exists
        ssa_tracked = IntervalSMTUtils.get_tracked_variable(callee_domain, first_ssa_name)
        if ssa_tracked is None:
            # Create it upfront with the constraint
            ssa_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, first_ssa_name, param_type
            )
            if ssa_tracked is None:
                return
            callee_domain.state.set_range_variable(first_ssa_name, ssa_tracked)
            ssa_tracked.assert_no_overflow(self.solver)

        # Constrain ONLY the first SSA version to equal the argument/constant value
        constraint: SMTTerm = ssa_tracked.term == rhs_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Created and constrained parameter SSA '{param}' to match argument/constant",
            param=first_ssa_name,
        )

    @staticmethod
    def _extract_ssa_index(ssa_suffix: str) -> int:
        """Extract a numeric SSA index from a suffix like 'x_2'. Returns -1 if unavailable."""
        if "_" in ssa_suffix:
            try:
                return int(ssa_suffix.split("_")[-1])
            except ValueError:
                return -1
        return -1
