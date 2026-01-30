"""Central interprocedural analysis logic for interval analysis."""

import time
from dataclasses import dataclass
from typing import List, Optional, Set, Protocol, runtime_checkable, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.analyses.data_flow.logger import get_logger
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


@runtime_checkable
class CallOperation(Protocol):
    """Protocol for call operations (InternalCall, LibraryCall, etc.)."""

    @property
    def function(self) -> Function: ...

    @property
    def arguments(self) -> List: ...

    @property
    def lvalue(self): ...


@dataclass
class ParameterInfo:
    """Info about a function parameter being constrained."""

    name: str
    tracked: TrackedSMTVariable
    type: ElementaryType


class InterproceduralAnalyzer:
    """Central class for interprocedural analysis across function calls.

    Consolidates shared logic for analyzing called functions, propagating state
    constraints through parameters, and merging results back to callers.
    """

    # Global call stack shared across all interprocedural analysis to detect recursion
    _call_stack: Set[Function] = set()

    def __init__(
        self,
        solver: "SMTSolver",
        analysis: "IntervalAnalysis",
        call_type_label: str = "function",
    ) -> None:
        """Initialize the interprocedural analyzer.

        Args:
            solver: SMT solver instance for constraint handling.
            analysis: Interval analysis instance for recursive analysis.
            call_type_label: Label for logging (e.g., "internal", "library").
        """
        self._solver = solver
        self._analysis = analysis
        self._call_type_label = call_type_label
        self._logger = get_logger()

    @property
    def solver(self) -> "SMTSolver":
        """Get the SMT solver instance."""
        return self._solver

    @property
    def analysis(self) -> "IntervalAnalysis":
        """Get the interval analysis instance."""
        return self._analysis

    @property
    def logger(self):
        """Get the logger instance."""
        return self._logger

    @classmethod
    def is_in_call_stack(cls, function: Function) -> bool:
        """Check if function is already being analyzed (cycle detection)."""
        return function in cls._call_stack

    @classmethod
    def add_to_call_stack(cls, function: Function) -> None:
        """Add function to the call stack."""
        cls._call_stack.add(function)

    @classmethod
    def remove_from_call_stack(cls, function: Function) -> None:
        """Remove function from the call stack."""
        cls._call_stack.discard(function)

    def analyze_call(
        self,
        operation: CallOperation,
        caller_domain: IntervalDomain,
    ) -> None:
        """Perform interprocedural analysis on a function call.

        Args:
            operation: The call operation (InternalCall, LibraryCall, etc.).
            caller_domain: The caller's domain state.
        """
        function = operation.function
        if not isinstance(function, Function):
            self.logger.debug(
                "{label} call function is not a Function instance, skipping",
                label=self._call_type_label.capitalize(),
            )
            return

        # Cycle detection
        if self.is_in_call_stack(function):
            self.logger.debug(
                "Recursion detected for {label} function '{name}', skipping analysis",
                label=self._call_type_label,
                name=function.name,
            )
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, caller_domain)
            return

        # Skip unimplemented functions
        if not function.nodes:
            self.logger.debug(
                "{label} function '{name}' has no nodes (not implemented), skipping",
                label=self._call_type_label.capitalize(),
                name=function.name,
            )
            if operation.lvalue is not None:
                self._handle_return_value_fallback(operation, caller_domain)
            return

        # Perform analysis with call stack protection
        self.add_to_call_stack(function)

        # NOTE: Removed push/pop optimization - it was causing constraint loss
        # for interprocedural variable linking. Need a more surgical approach.

        print(f"[INTERPROC] Starting analysis of {function.name}")
        start_time = time.time()
        try:
            self._analyze_called_function(operation, caller_domain, function)
        finally:
            elapsed = time.time() - start_time
            print(f"[INTERPROC] {function.name} completed in {elapsed:.2f}s")
            self.remove_from_call_stack(function)

    def _analyze_called_function(
        self,
        operation: CallOperation,
        caller_domain: IntervalDomain,
        called_function: Function,
    ) -> None:
        """Recursively analyze the called function with propagated state."""
        self.logger.debug(
            "Analyzing {label} function '{name}' interprocedurally",
            label=self._call_type_label,
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
            engine.state[entry_point.node_id] = AnalysisState(
                pre=callee_domain.deep_copy(), post=callee_domain.deep_copy()
            )

        # Run the analysis
        engine.run_analysis()

        # 4. Re-constrain parameters after analysis to ensure SSA versions are constrained
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
        operation: CallOperation,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
    ) -> None:
        """Constrain function parameters in callee domain based on caller arguments."""
        if not operation.arguments or not called_function.parameters:
            return

        for i, param in enumerate(called_function.parameters):
            if i >= len(operation.arguments):
                break
            self._constrain_single_parameter(
                operation.arguments[i], param, caller_domain, callee_domain
            )

    def _constrain_single_parameter(
        self,
        arg,
        param,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
    ) -> None:
        """Constrain a single parameter based on its corresponding argument."""
        param_name = IntervalSMTUtils.resolve_variable_name(param)
        param_type = IntervalSMTUtils.resolve_elementary_type(param.type)
        if param_name is None or param_type is None:
            return

        # Get or create parameter variable in callee domain
        param_tracked = self._get_or_create_param_tracked(
            callee_domain, param_name, param_type
        )
        if param_tracked is None:
            return

        # Handle constant argument
        if isinstance(arg, Constant):
            self._constrain_parameter_to_constant(
                param_name, param_tracked, arg.value, param_type, callee_domain
            )
            return

        # Handle variable argument
        param_info = ParameterInfo(param_name, param_tracked, param_type)
        self._constrain_parameter_to_variable(arg, param_info, caller_domain, callee_domain)

    def _get_or_create_param_tracked(
        self,
        callee_domain: IntervalDomain,
        param_name: str,
        param_type: ElementaryType,
    ) -> Optional[TrackedSMTVariable]:
        """Get or create the tracked variable for a parameter."""
        param_tracked = IntervalSMTUtils.get_tracked_variable(callee_domain, param_name)
        if param_tracked is None:
            param_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, param_name, param_type
            )
            if param_tracked is None:
                return None
            callee_domain.state.set_range_variable(param_name, param_tracked)
            param_tracked.assert_no_overflow(self.solver)
        return param_tracked

    def _constrain_parameter_to_variable(
        self,
        arg,
        param_info: ParameterInfo,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
    ) -> None:
        """Constrain a parameter to equal a variable argument."""
        arg_name = IntervalSMTUtils.resolve_variable_name(arg)
        if arg_name is None:
            return

        arg_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, arg_name)
        if arg_tracked is None:
            if hasattr(arg, "value"):
                self._constrain_parameter_to_constant(
                    param_info.name, param_info.tracked, arg.value,
                    param_info.type, callee_domain
                )
            return

        constraint: SMTTerm = param_info.tracked.term == arg_tracked.term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained {label} parameter '{param}' to equal argument '{arg}'",
            label=self._call_type_label,
            param=param_info.name,
            arg=arg_name,
        )

        self._constrain_parameter_ssa_versions(
            param_info.name, arg_tracked.term, param_info.type, callee_domain
        )

    def _reconstrain_parameters_after_analysis(
        self,
        operation: CallOperation,
        caller_domain: IntervalDomain,
        callee_domain: IntervalDomain,
        called_function: Function,
        engine: Engine,
    ) -> None:
        """Re-constrain parameters after analysis to ensure all SSA versions are constrained."""
        if not operation.arguments or not called_function.parameters:
            return

        all_domains = self._collect_analyzed_domains(called_function, engine)
        if not all_domains:
            return

        for i, param in enumerate(called_function.parameters):
            if i >= len(operation.arguments):
                break
            self._reconstrain_single_parameter(
                operation.arguments[i], param, caller_domain, all_domains
            )

    def _collect_analyzed_domains(
        self,
        called_function: Function,
        engine: Engine,
    ) -> List[IntervalDomain]:
        """Collect all domain states from analyzed nodes."""
        all_domains: List[IntervalDomain] = []
        for node in called_function.nodes:
            node_state = engine.state.get(node.node_id)
            if node_state and node_state.post.variant == DomainVariant.STATE:
                all_domains.append(node_state.post)
        return all_domains

    def _reconstrain_single_parameter(
        self,
        arg,
        param,
        caller_domain: IntervalDomain,
        all_domains: List[IntervalDomain],
    ) -> None:
        """Re-constrain a single parameter across all analyzed domains."""
        param_name = IntervalSMTUtils.resolve_variable_name(param)
        param_type = IntervalSMTUtils.resolve_elementary_type(param.type)
        if param_name is None or param_type is None:
            return

        rhs_term = self._resolve_rhs_term(arg, param_name, param_type, caller_domain, all_domains)
        if rhs_term is None:
            return

        for domain in all_domains:
            self._apply_parameter_constraint(domain, param_name, param_type, rhs_term)

    def _resolve_rhs_term(
        self,
        arg,
        param_name: str,
        param_type: ElementaryType,
        caller_domain: IntervalDomain,
        all_domains: List[IntervalDomain],
    ) -> Optional[SMTTerm]:
        """Resolve the RHS term for a parameter constraint."""
        if isinstance(arg, Constant):
            return self._resolve_constant_rhs(arg.value, param_name, param_type, all_domains)

        arg_name = IntervalSMTUtils.resolve_variable_name(arg)
        if arg_name is None:
            return None
        arg_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, arg_name)
        return arg_tracked.term if arg_tracked else None

    def _resolve_constant_rhs(
        self,
        const_value: int,
        param_name: str,
        param_type: ElementaryType,
        all_domains: List[IntervalDomain],
    ) -> Optional[SMTTerm]:
        """Resolve an RHS term for a constant argument."""
        for domain in all_domains:
            param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
            if param_tracked is not None:
                return self.solver.create_constant(const_value, param_tracked.sort)

        temp_tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, param_name, param_type
        )
        if temp_tracked is not None:
            return self.solver.create_constant(const_value, temp_tracked.sort)
        return None

    def _apply_parameter_constraint(
        self,
        domain: IntervalDomain,
        param_name: str,
        param_type: ElementaryType,
        rhs_term: SMTTerm,
    ) -> None:
        """Apply parameter constraint to a domain."""
        param_tracked = IntervalSMTUtils.get_tracked_variable(domain, param_name)
        if param_tracked is not None:
            constraint: SMTTerm = param_tracked.term == rhs_term
            self.solver.assert_constraint(constraint)
            self.logger.debug(
                "Re-constrained {label} base parameter '{param}'",
                label=self._call_type_label,
                param=param_name,
            )

        self._constrain_parameter_ssa_versions(param_name, rhs_term, param_type, domain)

    def _get_final_domain(self, function: Function, engine: Engine) -> Optional[IntervalDomain]:
        """Get the final domain state from function exit points (return statements)."""
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

        # Multiple return paths - merge them
        merged = final_domains[0].deep_copy()
        for other in final_domains[1:]:
            merged.join(other)
        return merged

    def _merge_callee_state_into_caller(
        self,
        caller_domain: IntervalDomain,
        callee_domain: Optional[IntervalDomain],
    ) -> None:
        """Merge callee's state modifications back into caller's domain."""
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
                    "Merged {label} state variable '{name}' from callee to caller",
                    label=self._call_type_label,
                    name=var_name,
                )
            else:
                caller_domain.state.set_range_variable(var_name, callee_tracked)
                self.logger.debug(
                    "Added new {label} state variable '{name}' from callee to caller",
                    label=self._call_type_label,
                    name=var_name,
                )

        for var_name, callee_op in callee_domain.state.get_binary_operations().items():
            if not caller_domain.state.has_binary_operation(var_name):
                caller_domain.state.set_binary_operation(var_name, callee_op)

    def _extract_return_value(
        self,
        operation: CallOperation,
        callee_domain: Optional[IntervalDomain],
        caller_domain: IntervalDomain,
    ) -> None:
        """Extract return value constraints from callee and assign to lvalue."""
        if callee_domain is None:
            self._handle_return_value_fallback(operation, caller_domain)
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if lvalue_name is None:
            return

        # Find the return value tracked variable
        return_tracked = self._find_return_value_tracked(operation, callee_domain)
        if return_tracked is None:
            self._handle_return_value_fallback(operation, caller_domain)
            return

        return_value_name, return_value_tracked = return_tracked

        # Determine return type and create lvalue variable
        return_type = self._determine_return_type(operation)
        if return_type is None:
            self.logger.debug(
                "Could not determine {label} return type for '{name}', using fallback",
                label=self._call_type_label,
                name=lvalue_name,
            )
            self._handle_return_value_fallback(operation, caller_domain)
            return

        lvalue_tracked = self._get_or_create_lvalue(
            caller_domain, lvalue_name, return_type
        )
        if lvalue_tracked is None:
            self._handle_return_value_fallback(operation, caller_domain)
            return

        # Apply the constraint
        constraint: SMTTerm = lvalue_tracked.term == return_value_tracked.term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Extracted {label} return value '{name}', constrained to '{return_name}'",
            label=self._call_type_label,
            name=lvalue_name,
            return_name=return_value_name,
        )

    def _find_return_value_tracked(
        self,
        operation: CallOperation,
        callee_domain: IntervalDomain,
    ) -> Optional[tuple[str, TrackedSMTVariable]]:
        """Find the tracked variable for the function's return value."""
        # Collect return values from function nodes
        return_values = self._collect_return_values(operation.function)
        if not return_values:
            self.logger.debug(
                "No return values found in {label} function, using fallback",
                label=self._call_type_label,
            )
            return None

        return_value = return_values[0]
        return_value_base = getattr(return_value, "canonical_name", None) or getattr(
            return_value, "name", None
        )

        if return_value_base is None:
            self.logger.debug(
                "{label} return value has no identifiable name, using fallback",
                label=self._call_type_label.capitalize(),
            )
            return None

        # Find the best matching tracked variable
        candidates = self._gather_return_candidates(callee_domain, return_value_base)
        if not candidates:
            self.logger.debug(
                "{label} return value base '{base}' not present in callee domain",
                label=self._call_type_label.capitalize(),
                base=return_value_base,
            )
            return None

        # Select the candidate with the highest SSA index (latest version)
        candidates.sort(key=lambda item: item[0])
        return_value_index, return_value_name, return_value_tracked = candidates[-1]
        self.logger.debug(
            "Selected {label} return value candidate '{name}' (ssa_index={index})",
            label=self._call_type_label,
            name=return_value_name,
            index=return_value_index,
        )
        return return_value_name, return_value_tracked

    def _collect_return_values(self, called_function: Function) -> List:
        """Collect all return values from the function's Return operations."""
        from slither.slithir.operations.return_operation import Return

        return_values = []
        for node in called_function.nodes:
            for ir in node.irs:
                if isinstance(ir, Return) and ir.values:
                    return_values.extend(ir.values)
        return return_values

    def _gather_return_candidates(
        self,
        callee_domain: IntervalDomain,
        return_value_base: str,
    ) -> List[tuple[int, str, TrackedSMTVariable]]:
        """Gather candidate variables matching the return value base name."""
        candidates: List[tuple[int, str, TrackedSMTVariable]] = []
        for var_name, tracked_var in callee_domain.state.get_range_variables().items():
            if var_name == return_value_base:
                candidates.append((-1, var_name, tracked_var))
            elif var_name.startswith(f"{return_value_base}|"):
                ssa_suffix = var_name.split("|", 1)[1]
                ssa_index = self._extract_ssa_index(ssa_suffix)
                candidates.append((ssa_index, var_name, tracked_var))
        return candidates

    def _determine_return_type(
        self,
        operation: CallOperation,
    ) -> Optional[ElementaryType]:
        """Determine the return type from the operation or function."""
        if hasattr(operation, "variable_return_type"):
            result = IntervalSMTUtils.resolve_elementary_type(operation.variable_return_type)
            if result is not None:
                return result

        called_function = operation.function
        if isinstance(called_function, Function) and called_function.return_type:
            result = IntervalSMTUtils.resolve_elementary_type(called_function.return_type)
            if result is not None:
                return result

        # Try to get type from return values
        return_values = self._collect_return_values(called_function)
        if return_values and hasattr(return_values[0], "type"):
            return IntervalSMTUtils.resolve_elementary_type(return_values[0].type)

        return None

    def _get_or_create_lvalue(
        self,
        caller_domain: IntervalDomain,
        lvalue_name: str,
        return_type: ElementaryType,
    ) -> Optional[TrackedSMTVariable]:
        """Get or create the lvalue tracked variable."""
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(caller_domain, lvalue_name)
        if lvalue_tracked is None:
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if lvalue_tracked is None:
                return None
            caller_domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)
        return lvalue_tracked

    def _handle_return_value_fallback(
        self,
        operation: CallOperation,
        domain: IntervalDomain,
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
        """Constrain a parameter (and its initial SSA version) to a constant value."""
        const_term: SMTTerm = self.solver.create_constant(const_value, param_tracked.sort)
        constraint: SMTTerm = param_tracked.term == const_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained {label} parameter '{param}' to constant value {value}",
            label=self._call_type_label,
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
        Subsequent SSA versions (_2, _3, etc.) are results of assignments.
        """
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
            "Created and constrained {label} parameter SSA '{param}'",
            label=self._call_type_label,
            param=first_ssa_name,
        )

    @staticmethod
    def _is_parameter_variable(var_name: str) -> bool:
        """Check if a variable name corresponds to a function parameter."""
        return "|" not in var_name or var_name.endswith("_0")

    @staticmethod
    def _extract_ssa_index(ssa_suffix: str) -> int:
        """Extract a numeric SSA index from a suffix like 'x_2'. Returns -1 if unavailable."""
        if "_" in ssa_suffix:
            try:
                return int(ssa_suffix.split("_")[-1])
            except ValueError:
                return -1
        return -1
