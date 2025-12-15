"""Handle high-level Solidity library calls in interval analysis."""

from typing import Optional, TYPE_CHECKING, List, Set

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class LibraryCallHandler(BaseOperationHandler):
    """Interprocedurally analyze library calls (modeled similarly to internal calls)."""

    # Class-level call stack to track recursion across all handler instances
    _call_stack: Set[Function] = set()

    def handle(self, operation: LibraryCall, domain: IntervalDomain, node: "Node") -> None:
        self.logger.debug("Handling library call: {operation}", operation=operation)

        # Guard: solver and analysis must be present
        if self.solver is None:
            self.logger.warning("Solver is None, skipping library call")
            return

        if self.analysis is None:
            self.logger.warning("Analysis instance is None, skipping interprocedural library call")
            return

        # Guard: only operate on concrete state domains
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping library call")
            return

        function = operation.function
        if not isinstance(function, Function):
            self.logger.debug("Library call function is not a Function instance, skipping")
            return

        # Cycle detection to avoid infinite recursion
        if function in LibraryCallHandler._call_stack:
            self.logger.debug(
                "Recursion detected for library function '{name}', skipping analysis",
                name=function.name,
            )
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, domain)
            return

        # Skip unimplemented library functions
        if not function.nodes:
            self.logger.debug(
                "Library function '{name}' has no nodes (not implemented), skipping",
                name=function.name,
            )
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, domain)
            return

        LibraryCallHandler._call_stack.add(function)
        try:
            self._analyze_called_function(operation, domain, function)
        finally:
            LibraryCallHandler._call_stack.discard(function)

    # The helpers below mirror the structure of InternalCallHandler, adapted for LibraryCall.

    def _analyze_called_function(
        self, operation: LibraryCall, caller_domain: IntervalDomain, called_function: Function
    ) -> None:
        """Recursively analyze the called library function with propagated state."""
        self.logger.debug(
            "Analyzing library function '{name}' interprocedurally",
            name=called_function.name,
        )

        callee_domain = IntervalDomain.with_state(caller_domain.state.deep_copy())

        self._constrain_parameters(operation, caller_domain, callee_domain, called_function)

        engine = Engine.new(analysis=self.analysis, function=called_function)

        entry_point = called_function.entry_point
        if entry_point is not None:
            engine.state[entry_point.node_id] = AnalysisState(
                pre=callee_domain.deep_copy(), post=callee_domain.deep_copy()
            )

        engine.run_analysis()

        self._reconstrain_parameters_after_analysis(
            operation, caller_domain, callee_domain, called_function, engine
        )

        final_domain = self._get_final_domain(called_function, engine)

        self._merge_callee_state_into_caller(caller_domain, final_domain)

        if operation.lvalue is not None:
            self._extract_return_value(operation, final_domain, caller_domain)

    def _constrain_parameters(
        self,
        operation: LibraryCall,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
    ) -> None:
        """Constrain library function parameters in callee domain based on caller arguments."""
        if not operation.arguments or not called_function.parameters:
            return

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

            param_tracked = IntervalSMTUtils.get_tracked_variable(callee_domain, param_name)
            if param_tracked is None:
                param_tracked = IntervalSMTUtils.create_tracked_variable(
                    self.solver, param_name, param_type
                )
                if param_tracked is None:
                    continue
                callee_domain.state.set_range_variable(param_name, param_tracked)
                param_tracked.assert_no_overflow(self.solver)

            if isinstance(arg, Constant):
                const_value = arg.value
                self._constrain_parameter_to_constant(
                    param_name=param_name,
                    param_tracked=param_tracked,
                    const_value=const_value,
                    param_type=param_type,
                    callee_domain=callee_domain,
                )
                continue

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

            constraint: SMTTerm = param_tracked.term == arg_tracked.term
            self.solver.assert_constraint(constraint)
            self.logger.debug(
                "Constrained library parameter '{param}' to equal argument '{arg}'",
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
        operation: LibraryCall,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
        engine: Engine,
    ) -> None:
        """Re-constrain library parameters after analysis to ensure SSA versions are constrained."""
        if not operation.arguments or not called_function.parameters:
            return

        all_domains: List[IntervalDomain] = []
        for node in called_function.nodes:
            node_state = engine.state.get(node.node_id)
            if node_state and node_state.post.variant == DomainVariant.STATE:
                all_domains.append(node_state.post)

        if not all_domains:
            return

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

            rhs_term: Optional[SMTTerm] = None
            if isinstance(arg, Constant):
                const_value = arg.value
                for domain in all_domains:
                    param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
                    if param_tracked is not None:
                        rhs_term = self.solver.create_constant(const_value, param_tracked.sort)
                        break
                if rhs_term is None:
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

            for domain in all_domains:
                param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
                if param_tracked is not None:
                    constraint: SMTTerm = param_tracked.term == rhs_term
                    self.solver.assert_constraint(constraint)
                    self.logger.debug(
                        "Re-constrained library base parameter '{param}'",
                        param=param_name,
                    )

                self._constrain_parameter_ssa_versions(
                    base_name=param_name,
                    rhs_term=rhs_term,
                    param_type=param_type,
                    callee_domain=domain,
                )

    def _get_final_domain(self, function: Function, engine: Engine) -> Optional[IntervalDomain]:
        """Get final domain state from library function exit points."""
        return_nodes = [node for node in function.nodes if not node.sons]

        if not return_nodes:
            if function.nodes:
                return_nodes = [function.nodes[-1]]
            else:
                return None

        final_domains: List[IntervalDomain] = []
        for return_node in return_nodes:
            node_state = engine.state.get(return_node.node_id)
            if node_state and node_state.post.variant == DomainVariant.STATE:
                final_domains.append(node_state.post)

        if not final_domains:
            return None

        if len(final_domains) == 1:
            return final_domains[0]

        merged = final_domains[0].deep_copy()
        for other in final_domains[1:]:
            merged.join(other)
        return merged

    def _merge_callee_state_into_caller(
        self, caller_domain: IntervalDomain, callee_domain: Optional[IntervalDomain]
    ) -> None:
        """Merge library callee state modifications back into caller domain."""
        if callee_domain is None or callee_domain.variant != DomainVariant.STATE:
            return

        for var_name, callee_tracked in callee_domain.state.get_range_variables().items():
            if self._is_parameter_variable(var_name):
                continue

            caller_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, var_name)
            if caller_tracked is not None:
                constraint: SMTTerm = caller_tracked.term == callee_tracked.term
                self.solver.assert_constraint(constraint)
                self.logger.debug(
                    "Merged library state variable '{name}' from callee to caller", name=var_name
                )
            else:
                caller_domain.state.set_range_variable(var_name, callee_tracked)
                self.logger.debug(
                    "Added new library state variable '{name}' from callee to caller",
                    name=var_name,
                )

        for var_name, callee_op in callee_domain.state.get_binary_operations().items():
            if not caller_domain.state.has_binary_operation(var_name):
                caller_domain.state.set_binary_operation(var_name, callee_op)

    def _extract_return_value(
        self,
        operation: LibraryCall,
        callee_domain: IntervalDomain,
        caller_domain: IntervalDomain,
    ) -> None:
        """Extract return value constraints from library callee and assign to lvalue."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        called_function = operation.function
        return_values = []
        for node in called_function.nodes:
            for ir in node.irs:
                from slither.slithir.operations.return_operation import Return

                if isinstance(ir, Return) and ir.values:
                    return_values.extend(ir.values)

        if not return_values:
            self.logger.debug(
                "No return values found in library function, using fallback",
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        return_value = return_values[0]
        return_value_base = getattr(return_value, "canonical_name", None) or getattr(
            return_value, "name", None
        )

        if return_value_base is None:
            self.logger.debug("Library return value has no identifiable name, using fallback")
            self._handle_return_value_fallback(operation, caller_domain)
            return

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
                "Library return value base '{base}' not present in callee domain, using fallback",
                base=return_value_base,
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        candidates.sort(key=lambda item: item[0])
        _, return_value_name, return_value_tracked = candidates[-1]
        self.logger.debug(
            "Selected library return value candidate '{name}'",
            name=return_value_name,
        )

        return_type: Optional[ElementaryType] = None
        if hasattr(operation, "variable_return_type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(operation.variable_return_type)
        if return_type is None and isinstance(called_function, Function):
            if called_function.return_type:
                return_type = IntervalSMTUtils.resolve_elementary_type(called_function.return_type)
        if return_type is None and hasattr(return_value, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(return_value.type)

        if return_type is None:
            self.logger.debug(
                "Could not determine library return type for '{name}', using fallback",
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

        constraint: SMTTerm = lvalue_tracked.term == return_value_tracked.term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Extracted library return value '{name}', constrained to '{return_name}'",
            name=lvalue_name,
            return_name=return_value_name,
        )

    def _is_parameter_variable(self, var_name: str) -> bool:
        """Heuristically check if a variable name corresponds to a function parameter."""
        return "|" not in var_name or var_name.endswith("_0")

    def _handle_return_value_fallback(
        self, operation: LibraryCall, domain: IntervalDomain
    ) -> None:
        """Fallback: create tracked variable for library return value without constraints."""
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
        if return_type is None and hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)
        function = operation.function
        if return_type is None and isinstance(function, Function) and function.return_type:
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
        """Constrain a library parameter (and its initial SSA version) to a constant value."""
        const_term: SMTTerm = self.solver.create_constant(const_value, param_tracked.sort)
        constraint: SMTTerm = param_tracked.term == const_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained library parameter '{param}' to constant value {value}",
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
        """Ensure the first SSA version for a library parameter equals the provided term."""
        base_var_name = (
            base_name.split(".")[-1]
            if "." in base_name
            else base_name.split("|")[-1] if "|" in base_name else base_name
        )

        first_ssa_name = f"{base_name}|{base_var_name}_1"

        ssa_tracked = IntervalSMTUtils.get_tracked_variable(callee_domain, first_ssa_name)
        if ssa_tracked is None:
            ssa_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, first_ssa_name, param_type
            )
            if ssa_tracked is None:
                return
            callee_domain.state.set_range_variable(first_ssa_name, ssa_tracked)
            ssa_tracked.assert_no_overflow(self.solver)

        constraint: SMTTerm = ssa_tracked.term == rhs_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Created and constrained library parameter SSA '{param}'",
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


