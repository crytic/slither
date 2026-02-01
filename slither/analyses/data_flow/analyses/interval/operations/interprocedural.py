"""Base handler for interprocedural analysis of function calls."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    constant_to_term,
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.return_operation import Return
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.variable import Variable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node
    from slither.slithir.operations.call import Call


@dataclass(frozen=True)
class CallContext:
    """Context for call analysis containing result metadata."""

    result_name: str
    result_type: ElementaryType
    call_prefix: str


class PrefixedStateWrapper:
    """Wrapper that prefixes variable names for namespaced call analysis."""

    def __init__(self, state: State, prefix: str) -> None:
        self._state = state
        self._prefix = prefix

    def get_variable(self, name: str) -> TrackedSMTVariable | None:
        """Get variable with prefixed name."""
        return self._state.get_variable(self._prefix + name)

    def set_variable(self, name: str, variable: TrackedSMTVariable) -> None:
        """Set variable with prefixed name."""
        self._state.set_variable(self._prefix + name, variable)


class PrefixedDomainWrapper:
    """Wrapper that provides prefixed state access for function call analysis."""

    def __init__(self, domain: "IntervalDomain", prefix: str) -> None:
        self._domain = domain
        self._prefix = prefix
        self._state = PrefixedStateWrapper(domain.state, prefix)

    @property
    def state(self) -> PrefixedStateWrapper:
        """Return prefixed state wrapper."""
        return self._state

    @property
    def variant(self):
        """Forward variant access to underlying domain."""
        return self._domain.variant

    @variant.setter
    def variant(self, value):
        """Forward variant setter to underlying domain."""
        self._domain.variant = value


class InterproceduralHandler(BaseOperationHandler):
    """Base handler for function calls requiring interprocedural analysis.

    Performs interprocedural analysis by mapping call arguments to
    function parameters and analyzing the function body.

    Subclasses should implement:
    - _get_called_function: Extract the Function object from the operation
    - _build_call_prefix: Generate unique prefix for this call site
    """

    def handle(
        self,
        operation: "Call",
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process call operation with interprocedural analysis."""
        if operation.lvalue is None:
            return

        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(operation.lvalue)
        called_function = self._get_called_function(operation)

        if called_function is None:
            self._create_unconstrained_result(result_name, lvalue_type, domain)
            return

        argument_terms = self._resolve_arguments(operation.arguments, domain)
        if argument_terms is None:
            self._create_unconstrained_result(result_name, lvalue_type, domain)
            return

        call_prefix = self._build_call_prefix(operation)
        context = CallContext(result_name, lvalue_type, call_prefix)
        self._analyze_called_function(called_function, argument_terms, domain, context)

    @abstractmethod
    def _get_called_function(self, operation: "Call") -> Function | None:
        """Extract the called Function from the operation."""

    @abstractmethod
    def _build_call_prefix(self, operation: "Call") -> str:
        """Build unique prefix for this call site."""

    def _resolve_arguments(
        self,
        arguments: List,
        domain: "IntervalDomain",
    ) -> List[SMTTerm] | None:
        """Resolve call arguments to SMT terms."""
        terms = []
        for arg in arguments:
            term = self._resolve_single_argument(arg, domain)
            if term is None:
                return None
            terms.append(term)
        return terms

    def _resolve_single_argument(
        self,
        argument,
        domain: "IntervalDomain",
    ) -> SMTTerm | None:
        """Resolve a single argument to an SMT term."""
        if isinstance(argument, Constant):
            return self._constant_to_term(argument)

        arg_name = get_variable_name(argument)
        tracked = domain.state.get_variable(arg_name)
        if tracked is not None:
            return tracked.term

        return None

    def _constant_to_term(self, constant: Constant) -> SMTTerm | None:
        """Convert a constant to an SMT term."""
        if not isinstance(constant.type, ElementaryType):
            return None
        value = constant.value
        if not isinstance(value, int):
            return None
        bit_width = get_bit_width(constant.type)
        return constant_to_term(self.solver, value, bit_width)

    def _analyze_called_function(
        self,
        function: Function,
        argument_terms: List[SMTTerm],
        domain: "IntervalDomain",
        context: CallContext,
    ) -> None:
        """Analyze called function with argument constraints."""
        parameters = function.parameters

        if len(parameters) != len(argument_terms):
            self._create_unconstrained_result(context.result_name, context.result_type, domain)
            return

        param_name_to_term = self._build_parameter_mapping(parameters, argument_terms)
        self._bind_parameter_reads(function, param_name_to_term, domain, context.call_prefix)
        self._analyze_function_body(function, domain, context.call_prefix)
        self._extract_return_value(function, domain, context)

    def _build_parameter_mapping(
        self,
        parameters: List,
        argument_terms: List[SMTTerm],
    ) -> Dict[str, SMTTerm]:
        """Build mapping from parameter base names to argument terms."""
        mapping: Dict[str, SMTTerm] = {}
        for param, arg_term in zip(parameters, argument_terms):
            mapping[param.name] = arg_term
        return mapping

    def _bind_parameter_reads(
        self,
        function: Function,
        param_name_to_term: Dict[str, SMTTerm],
        domain: "IntervalDomain",
        call_prefix: str,
    ) -> None:
        """Bind SSA parameter reads to argument values.

        Slither's SSA may use different versions for parameter definitions (a_0)
        vs reads in the function body (a_1). This method finds the actual
        read references and constrains them to argument values.
        """
        bound_names: set[str] = set()

        for node in function.nodes:
            for operation in node.irs_ssa:
                for var in operation.read:
                    self._bind_if_parameter(
                        var, param_name_to_term, domain, bound_names, call_prefix
                    )

    def _bind_if_parameter(
        self,
        variable: Variable,
        param_name_to_term: Dict[str, SMTTerm],
        domain: "IntervalDomain",
        bound_names: set[str],
        call_prefix: str,
    ) -> None:
        """Bind a variable to its argument value if it's a parameter read."""
        if not isinstance(variable, Variable):
            return

        base_name = variable.name
        if base_name not in param_name_to_term:
            return

        original_name = get_variable_name(variable)
        prefixed_name = call_prefix + original_name
        if prefixed_name in bound_names:
            return

        var_type = variable.type
        if not isinstance(var_type, ElementaryType):
            return

        arg_term = param_name_to_term[base_name]
        sort = type_to_sort(var_type)
        is_signed = is_signed_type(var_type)
        bit_width = get_bit_width(var_type)

        param_var = TrackedSMTVariable.create(
            self.solver, prefixed_name, sort, is_signed=is_signed, bit_width=bit_width
        )
        self.solver.assert_constraint(param_var.term == arg_term)
        domain.state.set_variable(prefixed_name, param_var)
        bound_names.add(prefixed_name)

    def _analyze_function_body(
        self,
        function: Function,
        domain: "IntervalDomain",
        call_prefix: str,
    ) -> None:
        """Analyze the function's body operations."""
        # Import here to avoid circular dependency (registry imports handlers)
        from slither.analyses.data_flow.analyses.interval.operations.registry import (
            OperationHandlerRegistry,
        )

        prefixed_domain = PrefixedDomainWrapper(domain, call_prefix)
        registry = OperationHandlerRegistry(self.solver)

        for node in function.nodes:
            for operation in node.irs_ssa:
                try:
                    handler = registry.get_handler(type(operation))
                    handler.handle(operation, prefixed_domain, node)
                except NotImplementedError:
                    continue

    def _extract_return_value(
        self,
        function: Function,
        domain: "IntervalDomain",
        context: CallContext,
    ) -> None:
        """Extract the return value from the analyzed function."""
        return_var = self._find_return_variable(function, domain, context.call_prefix)

        sort = type_to_sort(context.result_type)
        is_signed = is_signed_type(context.result_type)
        bit_width = get_bit_width(context.result_type)

        result_var = TrackedSMTVariable.create(
            self.solver, context.result_name, sort, is_signed=is_signed, bit_width=bit_width
        )

        if return_var is not None:
            self.solver.assert_constraint(result_var.term == return_var.term)

        domain.state.set_variable(context.result_name, result_var)

    def _find_return_variable(
        self,
        function: Function,
        domain: "IntervalDomain",
        call_prefix: str,
    ) -> TrackedSMTVariable | None:
        """Find the return variable from the function's return operations."""
        for node in function.nodes:
            for operation in node.irs_ssa:
                if not isinstance(operation, Return):
                    continue
                if not operation.values:
                    continue
                return_val = operation.values[0]
                return_name = call_prefix + get_variable_name(return_val)
                return domain.state.get_variable(return_name)

        return None

    def _create_unconstrained_result(
        self,
        name: str,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Create an unconstrained variable for fallback cases."""
        sort = type_to_sort(element_type)
        is_signed = is_signed_type(element_type)
        bit_width = get_bit_width(element_type)

        result_var = TrackedSMTVariable.create(
            self.solver, name, sort, is_signed=is_signed, bit_width=bit_width
        )
        domain.state.set_variable(name, result_var)
