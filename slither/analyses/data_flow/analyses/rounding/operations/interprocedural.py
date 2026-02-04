"""Base handler for interprocedural analysis of function calls."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
    infer_tag_from_name,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.return_operation import Return

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.operations.registry import (
        OperationHandlerRegistry,
    )


def _create_registry(analysis: "BaseOperationHandler") -> "OperationHandlerRegistry":
    """Create operation handler registry, avoiding circular import at module level."""
    from slither.analyses.data_flow.analyses.rounding.operations.registry import (
        OperationHandlerRegistry,
    )

    return OperationHandlerRegistry(analysis.analysis)


class InterproceduralHandler(BaseOperationHandler):
    """Base handler for function calls requiring interprocedural analysis.

    Subclasses should implement:
    - _get_called_function: Extract the Function object from the operation
    - _get_function_name: Get the function name for name-based inference
    """

    def __init__(self, analysis) -> None:
        super().__init__(analysis)
        self._call_stack: set[Function] = set()

    def handle(
        self,
        operation: Call,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Process call with name-based inference, falling back to body analysis."""
        if not operation.lvalue:
            return

        function_name = self._get_function_name(operation)

        if self._is_named_division_function(function_name):
            self._check_named_division_consistency(operation, domain, node)

        tag = self._infer_tag_with_fallback(operation, function_name, domain)
        self._set_tag(operation.lvalue, tag, operation, node, domain)

    def _infer_tag_with_fallback(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
    ) -> RoundingTag:
        """Infer tag from name first, then fall back to body analysis."""
        tag = infer_tag_from_name(function_name)
        if tag != RoundingTag.NEUTRAL:
            return tag

        called_function = self._get_called_function(operation)
        if called_function is None:
            return tag

        body_tag = self._analyze_function_body(
            called_function, operation.arguments, domain
        )
        return body_tag if body_tag is not None else tag

    @abstractmethod
    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function, or None if not resolvable."""

    @abstractmethod
    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""

    def _analyze_function_body(
        self,
        function: Function,
        arguments: list,
        domain: RoundingDomain,
    ) -> RoundingTag | None:
        """Analyze function body with argument tag mapping.

        Returns the tag of the return value, or None if analysis fails.
        """
        if function in self._call_stack:
            return RoundingTag.UNKNOWN

        if not function.nodes:
            return None

        self._call_stack.add(function)
        try:
            return self._run_interprocedural_analysis(function, arguments, domain)
        finally:
            self._call_stack.discard(function)

    def _run_interprocedural_analysis(
        self,
        function: Function,
        arguments: list,
        domain: RoundingDomain,
    ) -> RoundingTag | None:
        """Run analysis on callee function and extract return tag."""
        callee_domain = RoundingDomain(DomainVariant.STATE, RoundingState())
        self._bind_parameter_tags(function, arguments, domain, callee_domain)
        self._analyze_callee_body(function, callee_domain)
        return self._extract_return_tag(function, callee_domain)

    def _bind_parameter_tags(
        self,
        function: Function,
        arguments: list,
        caller_domain: RoundingDomain,
        callee_domain: RoundingDomain,
    ) -> None:
        """Map argument tags from caller to parameter variables in callee."""
        for parameter, argument in zip(function.parameters, arguments):
            argument_tag = get_variable_tag(argument, caller_domain)
            callee_domain.state.set_tag(parameter, argument_tag)

    def _analyze_callee_body(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> None:
        """Analyze the function body operations."""
        registry = _create_registry(self)
        for node in function.nodes:
            self._analyze_node_operations(node, callee_domain, registry)

    def _analyze_node_operations(
        self,
        node: Node,
        callee_domain: RoundingDomain,
        registry: "OperationHandlerRegistry",
    ) -> None:
        """Analyze all operations in a single node."""
        if not node.irs_ssa:
            return
        for operation in node.irs_ssa:
            handler = registry.get_handler(type(operation))
            if handler is not None:
                handler.handle(operation, callee_domain, node)

    def _extract_return_tag(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> RoundingTag | None:
        """Extract the return value's tag from the analyzed function."""
        for node in function.nodes:
            tag = self._get_return_tag_from_node(node, callee_domain)
            if tag is not None:
                return tag
        return None

    def _get_return_tag_from_node(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> RoundingTag | None:
        """Get return tag from a single node if it contains a return operation."""
        if not node.irs_ssa:
            return None
        for operation in node.irs_ssa:
            if not isinstance(operation, Return):
                continue
            if not operation.values:
                continue
            return_value = operation.values[0]
            if isinstance(return_value, Variable):
                return callee_domain.state.get_tag(return_value)
        return None

    def _is_named_division_function(self, function_name: str) -> bool:
        """Return True when function name indicates divUp/divDown helpers."""
        name_lower = function_name.lower()
        return "divup" in name_lower or "divdown" in name_lower

    def _check_named_division_consistency(
        self,
        operation: Call,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Enforce division consistency for divUp/divDown call arguments."""
        if len(operation.arguments) < 2:
            return

        numerator = operation.arguments[0]
        denominator = operation.arguments[1]
        numerator_tag = get_variable_tag(numerator, domain)
        denominator_tag = get_variable_tag(denominator, domain)
        inconsistency_reason = self._check_division_consistency(
            numerator_tag, denominator_tag, operation, node
        )
        if inconsistency_reason and operation.lvalue:
            domain.state.set_tag(
                operation.lvalue,
                RoundingTag.UNKNOWN,
                operation,
                unknown_reason=inconsistency_reason,
            )

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Call,
        node: Node,
    ) -> Optional[str]:
        """Check numerator/denominator consistency for division operations."""
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        if numerator_tag != denominator_tag:
            return None

        function_name = node.function.name
        reason = (
            "Inconsistent division: numerator and denominator both "
            f"{numerator_tag.name} in {function_name}"
        )
        message = (
            "Division rounding inconsistency in "
            f"{function_name}: numerator and denominator both "
            f"{numerator_tag.name} in {operation}"
        )
        self.analysis.inconsistencies.append(message)
        self.analysis._logger.error(message)
        return reason

    def _set_tag(
        self,
        variable: object,
        tag: RoundingTag,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Set tag and check annotation."""
        if not isinstance(variable, Variable):
            return
        domain.state.set_tag(variable, tag, operation)
        self.analysis._check_annotation_for_variable(
            variable, tag, operation, node, domain
        )
