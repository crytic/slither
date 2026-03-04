"""Base handler for interprocedural analysis of function calls."""

from __future__ import annotations

from abc import abstractmethod

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.core.models import RoundingFinding
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
    infer_tag_from_name,
    lookup_inline_round_tag,
    lookup_known_tag,
)
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables.tuple import TupleVariable

_logger = get_logger()


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
            _logger.debug("Call has no lvalue, skipping: {op}", op=operation)
            return

        function_name = self._get_function_name(operation)

        if self._is_named_division_function(function_name):
            self._check_named_division_consistency(operation, domain, node)

        if isinstance(operation.lvalue, TupleVariable):
            self._handle_tuple_call(operation, function_name, domain, node)
            return

        tags, trace = self._infer_tag_with_fallback(
            operation, function_name, domain, node
        )
        self._set_tags(operation.lvalue, tags, operation, node, domain, trace)

    def _handle_tuple_call(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Handle a call whose lvalue is a TupleVariable.

        Resolves the callee, runs interprocedural analysis, then sets
        tags directly on Unpack lvalues found in the same node.
        """
        called_function = self._get_called_function(operation)
        if called_function is None or not called_function.nodes:
            _logger.debug(
                "Tuple call {name}: callee unresolvable or has no body",
                name=function_name,
            )
            return

        if called_function in self._call_stack:
            _logger.debug(
                "Tuple call {name}: recursion guard, skipping",
                name=function_name,
            )
            return

        self._call_stack.add(called_function)
        try:
            callee_domain = RoundingDomain(DomainVariant.STATE, RoundingState())
            self._bind_parameter_tags(
                called_function,
                operation.arguments,
                domain,
                callee_domain,
            )
            self._analyze_callee_body(called_function, callee_domain)
            per_index = self._extract_per_index_return_tags(
                called_function, callee_domain
            )
        finally:
            self._call_stack.discard(called_function)

        if not per_index:
            _logger.error_and_raise(
                "Tuple call {name}: analyzed body but found no return tags",
                RuntimeError,
                name=function_name,
            )

        line_number = node.source_mapping.lines[0] if node.source_mapping else None
        self._apply_tuple_tags_to_unpacks(
            operation,
            per_index,
            function_name,
            line_number,
            domain,
            node,
        )

    def _apply_tuple_tags_to_unpacks(
        self,
        operation: Call,
        per_index: list[tuple[TagSet, list[TraceNode]]],
        function_name: str,
        line_number: int | None,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Set per-index tags directly on Unpack lvalues in this node."""
        all_tags: set[RoundingTag] = set()
        for other_operation in node.irs_ssa:
            if not isinstance(other_operation, Unpack):
                continue
            if other_operation.tuple != operation.lvalue:
                continue
            if other_operation.lvalue is None:
                continue
            index = other_operation.index
            if index >= len(per_index):
                _logger.warning(
                    "Tuple call {name}: unpack index {idx} exceeds "
                    "return count {count}, skipping",
                    name=function_name,
                    idx=index,
                    count=len(per_index),
                )
                continue
            tags, traces = per_index[index]
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=tags,
                source=(f"{function_name}()[{index}] → {_format_tagset(tags)}"),
                children=traces,
            )
            domain.state.set_tag(
                other_operation.lvalue,
                tags,
                other_operation,
                trace=trace,
            )
            all_tags.update(tags)

        if all_tags:
            combined = frozenset(all_tags)
            domain.state.set_tag(
                operation.lvalue,
                combined,
                operation,
            )

    def _extract_per_index_return_tags(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> list[tuple[TagSet, list[TraceNode]]]:
        """Extract per-index return tags from a tuple-returning function."""
        for node in function.nodes:
            if not node.irs_ssa:
                continue
            for operation in node.irs_ssa:
                if not isinstance(operation, Return):
                    continue
                if not operation.values:
                    continue
                condition = _find_branch_condition(node)
                results: list[tuple[TagSet, list[TraceNode]]] = []
                for return_value in operation.values:
                    if isinstance(return_value, TupleVariable):
                        tuple_tags = callee_domain.state.get_tags(
                            return_value,
                        )
                        if not tuple_tags:
                            tuple_tags = frozenset({RoundingTag.NEUTRAL})
                        tuple_trace = callee_domain.state.get_trace(
                            return_value,
                        )
                        trace_list = [tuple_trace] if tuple_trace else []
                        return_types = function.return_type or []
                        count = max(len(return_types), 1)
                        for _ in range(count):
                            results.append((tuple_tags, list(trace_list)))
                    elif isinstance(return_value, Variable):
                        tags = callee_domain.state.get_tags(return_value)
                        trace = callee_domain.state.get_trace(return_value)
                        if trace is not None:
                            trace.branch_condition = condition
                        trace_list = [trace] if trace else []
                        results.append((tags, trace_list))
                    else:
                        neutral = frozenset({RoundingTag.NEUTRAL})
                        results.append((neutral, []))
                return results
        return []

    def _lookup_inline_annotation(
        self,
        node: Node,
        function_name: str,
    ) -> RoundingTag | None:
        """Check for an inline //@round annotation matching a function call.

        Scans all source lines of the node for //@round annotations
        and returns the tag for the given function name if found.

        Args:
            node: The CFG node containing the call.
            function_name: The function name to look up.

        Returns:
            RoundingTag if annotated, None otherwise.
        """
        if node.source_mapping is None:
            return None
        filename = node.source_mapping.filename.absolute
        crytic = node.compilation_unit.core.crytic_compile
        for line_number in node.source_mapping.lines:
            raw_bytes = crytic.get_code_from_line(filename, line_number)
            if raw_bytes is None:
                continue
            tag = lookup_inline_round_tag(raw_bytes.decode("utf8"), function_name)
            if tag is not None:
                return tag
        return None

    def _infer_tag_with_fallback(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
        node: Node,
    ) -> tuple[TagSet, TraceNode | None]:
        """Infer tags: inline annotation > name > known library > body analysis.

        Returns (tags, trace) where trace captures the call provenance if available.
        """
        line_number = node.source_mapping.lines[0] if node.source_mapping else None

        inline_tag = self._lookup_inline_annotation(node, function_name)
        if inline_tag is not None:
            _logger.debug(
                "{name}: resolved via inline annotation → {tag}",
                name=function_name,
                tag=inline_tag.name,
            )
            inline_tags = frozenset({inline_tag})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=inline_tags,
                source=f"{function_name}() → {inline_tag.name} (inline annotation)",
            )
            return inline_tags, trace

        tag = infer_tag_from_name(function_name)
        if tag != RoundingTag.NEUTRAL:
            _logger.debug(
                "{name}: resolved via name inference → {tag}",
                name=function_name,
                tag=tag.name,
            )
            tags = frozenset({tag})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=tags,
                source=f"{function_name}() → {tag.name}",
            )
            return tags, trace

        called_function = self._get_called_function(operation)
        if called_function is None:
            _logger.debug(
                "{name}: callee unresolvable, defaulting to NEUTRAL",
                name=function_name,
            )
            return frozenset({tag}), None

        known = _lookup_known_function_tag(
            called_function, function_name, self.analysis.known_tags
        )
        if known is not None:
            _logger.debug(
                "{name}: resolved via known library → {tag}",
                name=function_name,
                tag=known.name,
            )
            known_tags = frozenset({known})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=known_tags,
                source=f"{function_name}() → {known.name} (known library)",
            )
            return known_tags, trace

        body_tags, child_traces = self._analyze_function_body(
            called_function, operation.arguments, domain
        )
        if body_tags:
            _logger.debug(
                "{name}: resolved via body analysis → {tags}",
                name=function_name,
                tags=_format_tagset(body_tags),
            )
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=body_tags,
                source=f"{function_name}() returns {_format_tagset(body_tags)}",
                children=child_traces,
            )
            return body_tags, trace
        _logger.debug(
            "{name}: all inference steps exhausted, defaulting to NEUTRAL",
            name=function_name,
        )
        return frozenset({tag}), None

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
    ) -> tuple[TagSet | None, list[TraceNode]]:
        """Analyze function body with argument tag mapping.

        Returns (tags, child_traces) where tags is the set of all return value tags,
        and child_traces contains provenance from nested calls.
        """
        if function in self._call_stack:
            _logger.debug(
                "Recursion guard: {name} already in call stack",
                name=function.name,
            )
            return frozenset({RoundingTag.UNKNOWN}), []

        if not function.nodes:
            _logger.debug(
                "Function {name} has no body nodes, skipping analysis",
                name=function.name,
            )
            return None, []

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
    ) -> tuple[TagSet | None, list[TraceNode]]:
        """Run analysis on callee function and extract return tags and traces."""
        callee_domain = RoundingDomain(DomainVariant.STATE, RoundingState())
        self._bind_parameter_tags(function, arguments, domain, callee_domain)
        self._analyze_callee_body(function, callee_domain)
        tags = self._extract_return_tags(function, callee_domain)
        traces = self._extract_return_traces(function, callee_domain)
        return tags, traces

    def _bind_parameter_tags(
        self,
        function: Function,
        arguments: list,
        caller_domain: RoundingDomain,
        callee_domain: RoundingDomain,
    ) -> None:
        """Map argument tags from caller to parameter variables in callee.

        Binds tags to SSA variable reads by matching base names, since Slither's
        SSA uses different variable instances for parameters vs body reads.
        """
        param_name_to_tag: dict[str, RoundingTag] = {}
        for parameter, argument in zip(function.parameters, arguments):
            argument_tag = get_variable_tag(argument, caller_domain)
            callee_domain.state.set_tag(parameter, argument_tag)
            param_name_to_tag[parameter.name] = argument_tag

        # Bind to SSA variable reads in the function body
        bound_vars: set[Variable] = set()
        for node in function.nodes:
            if not node.irs_ssa:
                continue
            for operation in node.irs_ssa:
                for var in operation.read:
                    if not isinstance(var, Variable):
                        continue
                    if var in bound_vars:
                        continue
                    if var.name in param_name_to_tag:
                        callee_domain.state.set_tag(var, param_name_to_tag[var.name])
                        bound_vars.add(var)

    def _analyze_callee_body(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> None:
        """Analyze the function body operations."""
        for node in function.nodes:
            self._analyze_node_operations(node, callee_domain)

    def _analyze_node_operations(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> None:
        """Analyze all operations in a single node."""
        if not node.irs_ssa:
            return
        for operation in node.irs_ssa:
            handler = self.analysis._registry.get_handler(type(operation))
            if handler is not None:
                handler.handle(operation, callee_domain, node)

    def _extract_return_tags(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> TagSet | None:
        """Extract all return value tags from the analyzed function."""
        all_tags: set[RoundingTag] = set()
        for node in function.nodes:
            tags = self._get_return_tags_from_node(node, callee_domain)
            all_tags.update(tags)
        if not all_tags:
            return None
        if len(all_tags) > 1 and RoundingTag.NEUTRAL in all_tags:
            all_tags.discard(RoundingTag.NEUTRAL)
        return frozenset(all_tags)

    def _get_return_tags_from_node(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> set[RoundingTag]:
        """Get return tags from a single node if it contains a return operation."""
        tags: set[RoundingTag] = set()
        if not node.irs_ssa:
            return tags
        for operation in node.irs_ssa:
            if not isinstance(operation, Return):
                continue
            if not operation.values:
                continue
            return_value = operation.values[0]
            if isinstance(return_value, Variable):
                tags.update(callee_domain.state.get_tags(return_value))
        return tags

    def _extract_return_traces(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> list[TraceNode]:
        """Extract traces from return values in the analyzed function."""
        traces: list[TraceNode] = []
        for node in function.nodes:
            traces.extend(self._get_return_traces_from_node(node, callee_domain))
        return traces

    def _get_return_traces_from_node(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> list[TraceNode]:
        """Get traces from return values in a single node."""
        traces: list[TraceNode] = []
        if not node.irs_ssa:
            return traces
        for operation in node.irs_ssa:
            if not isinstance(operation, Return):
                continue
            if not operation.values:
                continue
            return_value = operation.values[0]
            if isinstance(return_value, Variable):
                trace = callee_domain.state.get_trace(return_value)
                if trace is not None:
                    trace.branch_condition = _find_branch_condition(node)
                    traces.append(trace)
        return traces

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
    ) -> str | None:
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
        self.analysis.inconsistencies.append(
            RoundingFinding(message=message, node=node)
        )
        self.analysis._logger.warning(message)
        return reason

    def _set_tag(
        self,
        variable: Variable | None,
        tag: RoundingTag,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Set tag and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tag, operation)
        self.analysis._check_annotation_for_variable(
            variable, tag, operation, node, domain
        )

    def _set_tags(
        self,
        variable: Variable | None,
        tags: TagSet,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
        trace: TraceNode | None = None,
    ) -> None:
        """Set tag set, trace, and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tags, operation, trace=trace)
        actual_tag = domain.state.get_tag(variable)
        self.analysis._check_annotation_for_variable(
            variable, actual_tag, operation, node, domain
        )


def _find_branch_condition(node: Node) -> str | None:
    """Find the IF condition guarding a CFG node, if any.

    Walks up the immediate-dominator chain. When an IF node is found,
    determines whether the original node is in the true or false branch
    by checking which son dominates it.
    """
    current = node
    while current.immediate_dominator is not None:
        idom = current.immediate_dominator
        if idom.type == NodeType.IF and idom.expression is not None:
            if _is_in_true_branch(idom, node):
                return str(idom.expression)
            if _is_in_false_branch(idom, node):
                return f"!({idom.expression})"
            break
        current = idom
    return None


def _is_in_true_branch(if_node: Node, target: Node) -> bool:
    """Check if target is dominated by the true branch of if_node."""
    son_true = if_node.son_true
    if son_true is None:
        return False
    return son_true == target or son_true in target.dominators


def _is_in_false_branch(if_node: Node, target: Node) -> bool:
    """Check if target is dominated by the false branch of if_node."""
    son_false = if_node.son_false
    if son_false is None:
        return False
    return son_false == target or son_false in target.dominators


def _lookup_known_function_tag(
    called_function: Function,
    function_name: str,
    known_tags: dict[tuple[str, str], RoundingTag] | None,
) -> RoundingTag | None:
    """Check if function matches a known library rounding pattern."""
    if known_tags is None:
        return None
    if not isinstance(called_function, FunctionContract):
        return None
    return lookup_known_tag(
        called_function.contract_declarer.name, function_name, known_tags
    )


def _format_tagset(tags: TagSet) -> str:
    """Format a tag set for display in trace sources."""
    if len(tags) == 1:
        return next(iter(tags)).name
    names = sorted(tag.name for tag in tags)
    return "{" + ", ".join(names) + "}"
