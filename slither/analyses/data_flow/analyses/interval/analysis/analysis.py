"""Interval analysis implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.analysis.loop import (
    PRECISE_LOOP_GENERATION_LIMIT,
    IntervalLoopMetadata,
)
from slither.analyses.data_flow.analyses.interval.core.state import ComparisonInfo, State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.loop import (
    LoopVariableId,
    LoopWideningContext,
    LoopWideningResult,
)
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.facts import (
    AnalysisContextId,
    Fact,
    FactId,
    FactKind,
    FactOriginKind,
    FactOwnerKind,
    FactProvenance,
    LoopHeaderId,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation
from slither.slithir.variables.constant import Constant


if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.types import SMTTerm
    from slither.core.variables.local_variable import LocalVariable

logger = get_logger()


class IntervalAnalysis(Analysis):
    """Forward interval analysis using SMT constraints."""

    def __init__(self, solver: SMTSolver, timeout_ms: int) -> None:
        self._direction: Direction = Forward()
        self._solver: SMTSolver = solver
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self._solver)
        self._thresholds: list[int] = []
        self._timeout_ms: int = timeout_ms
        self._root_context = AnalysisContextId.unbound()
        self._loop_metadata = IntervalLoopMetadata()

    @property
    def solver(self) -> SMTSolver:
        return self._solver

    def domain(self) -> Domain:
        return IntervalDomain.with_state(State({}, context_id=self._root_context))

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom(self._root_context)

    def prepare_for_function(self, function: Function) -> None:
        """Collect numeric literals from function for threshold widening."""
        self._root_context = AnalysisContextId.root(function)
        self._solver.bind_function_encoding(self._root_context.encoding_id)
        self._thresholds = self._collect_thresholds(function)
        self._loop_metadata = IntervalLoopMetadata.from_function(function)
        self._registry.configure_loop_metadata(self._loop_metadata)
        logger.debug(
            "Collected {count} thresholds for {name}: {thresholds}",
            count=len(self._thresholds),
            name=function.name,
            thresholds=self._thresholds[:20],
        )

    def _collect_thresholds(self, function: Function) -> list[int]:
        """Extract all numeric constants from function's IR.

        Returns a sorted list in increasing order, bounded by type extremes.
        The list always includes 0 and the uint256 min/max as final fallbacks.
        """
        # Type extremes for uint256 (most common case)
        type_min = 0
        type_max = (1 << 256) - 1

        threshold_set: set[int] = {0, type_min, type_max}

        for node in function.nodes:
            self._extract_constants_from_node(node, threshold_set)

        return sorted(threshold_set)

    def _extract_constants_from_node(self, node: Node, threshold_set: set[int]) -> None:
        """Extract numeric constants from a single CFG node."""
        for operation in node.irs_ssa or []:
            for operand in operation.read:
                self._add_constant_threshold(operand, threshold_set)

    def _add_constant_threshold(self, operand: object, threshold_set: set[int]) -> None:
        """Add constant value to threshold set if it's a numeric constant."""
        if not isinstance(operand, Constant):
            return

        value = operand.value
        if not isinstance(value, int):
            return

        threshold_set.add(value)

    @property
    def thresholds(self) -> list[int]:
        """Return the sorted list of widening thresholds."""
        return self._thresholds

    def loop_variables(self, header_id: LoopHeaderId) -> tuple[LoopVariableId, ...]:
        """Return the loop-carried SSA bindings for one stable header."""
        return self._loop_metadata.variables_for(header_id)

    def transfer_function(
        self,
        node: Node,
        domain: Domain,
        operation: Operation | None,
    ) -> None:
        if not isinstance(domain, IntervalDomain):
            raise TypeError("IntervalAnalysis requires an IntervalDomain")
        self._transfer_function_helper(node, domain, operation)

    def _transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
        if domain.variant == DomainVariant.TOP:
            return

        if domain.variant == DomainVariant.BOTTOM:
            if domain.state is not None:
                return  # Detected unreachable path - skip further processing
            self._initialize_domain_from_bottom(domain)

        self._handle_variable_declaration(node, domain)
        self._dispatch_operation(operation, domain, node)

    def _initialize_domain_from_bottom(self, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom."""
        domain.variant = DomainVariant.STATE
        domain.state = State({}, context_id=self._root_context)

    def _handle_variable_declaration(
        self,
        node: Node,
        domain: IntervalDomain,
    ) -> None:
        """Handle variable declaration nodes by initializing to zero.

        In Solidity, uninitialized local variables have default zero values.
        This method processes NodeType.VARIABLE nodes that have no initializer,
        creating a tracked variable constrained to zero.
        """
        if node.type != NodeType.VARIABLE:
            return

        variable_declaration = node.variable_declaration
        if variable_declaration is None:
            return

        if not self._is_uninitialized_declaration(node, variable_declaration):
            return

        self._initialize_variable_to_zero(node, variable_declaration, domain)

    def _is_uninitialized_declaration(
        self,
        node: Node,
        variable: LocalVariable,
    ) -> bool:
        """Check if a variable declaration has no initializer.

        Returns True if the variable is declared without an explicit value
        and the node has no SSA operations (which would indicate an initializer).
        """
        if node.irs_ssa:
            return False

        if not isinstance(variable.type, ElementaryType):
            return False

        return True

    def _initialize_variable_to_zero(
        self,
        node: Node,
        variable: LocalVariable,
        domain: IntervalDomain,
    ) -> None:
        """Create a tracked variable initialized to zero."""
        variable_type = variable.type
        if not isinstance(variable_type, ElementaryType):
            return

        variable_name = f"{variable.name}_0"
        sort = type_to_sort(variable_type)
        bit_width = get_bit_width(variable_type)
        signed = is_signed_type(variable_type)

        tracked = TrackedSMTVariable.create(
            self._solver, variable_name, sort, is_signed=signed, bit_width=bit_width
        ).with_interval(NumericInterval(0, 0))

        zero_term = self._solver.create_constant(0, sort)
        operation_id = StaticOperationId.synthetic(node)
        fact = Fact(
            fact_id=FactId(
                owner=FactOwnerKind.IMMUTABLE_EQUATION,
                kind=FactKind.VALUE_BINDING,
                provenance=FactProvenance(
                    context_id=domain.context_id,
                    origin_kind=FactOriginKind.FUNCTION_ENTRY,
                    operation_id=operation_id,
                ),
                semantic_key=("uninitialized_default", variable_name),
            ),
            formula=tracked.term == zero_term,
        )
        self._solver.register_immutable_fact(fact)

        if domain.state is None:
            raise ValueError("Initialized interval domain has no State")
        domain.state.set_variable(variable_name, tracked)

    def _dispatch_operation(
        self,
        operation: Operation | None,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Dispatch operation to appropriate handler."""
        if operation is None:
            return

        # Record telemetry for operation category
        self._record_operation_telemetry(operation)

        handler = self._registry.get_handler(type(operation))
        handler.handle(operation, domain, node)

    def _record_operation_telemetry(self, operation: Operation) -> None:
        """Record operation category in telemetry."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return

        telemetry.record_transfer_op(self._operation_category(operation), handled=True)

    @staticmethod
    def _operation_category(operation: Operation) -> str:
        """Classify one transfer operation for opt-in telemetry."""
        from slither.slithir.operations import Assignment
        from slither.slithir.operations.binary import Binary
        from slither.slithir.operations.high_level_call import HighLevelCall
        from slither.slithir.operations.internal_call import InternalCall
        from slither.slithir.operations.library_call import LibraryCall
        from slither.slithir.operations.solidity_call import SolidityCall
        from slither.slithir.operations.unary import Unary

        operation_type = type(operation)
        if operation_type is Binary:
            return IntervalAnalysis._binary_operation_category(operation)
        if operation_type is Unary:
            return "arithmetic"
        if operation_type is SolidityCall:
            return IntervalAnalysis._solidity_call_category(operation)
        if operation_type in (HighLevelCall, InternalCall, LibraryCall):
            return "call"
        if operation_type is Condition:
            return "comparison"
        if operation_type is Assignment:
            return "assignment"
        return "assignment"

    @staticmethod
    def _binary_operation_category(operation: Operation) -> str:
        operation_kind = getattr(operation, "type", None)
        operation_name = str(getattr(operation_kind, "name", ""))
        if operation_name in {
            "LESS",
            "GREATER",
            "LESS_EQUAL",
            "GREATER_EQUAL",
            "EQUAL",
            "NOT_EQUAL",
        }:
            return "comparison"
        if operation_name in {
            "AND",
            "OR",
            "LEFT_SHIFT",
            "RIGHT_SHIFT",
            "CARET",
            "OROR",
            "ANDAND",
        }:
            return "bitwise"
        return "arithmetic"

    @staticmethod
    def _solidity_call_category(operation: Operation) -> str:
        function = getattr(operation, "function", None)
        function_name = str(function) if function else ""
        if "mstore" in function_name or "mload" in function_name:
            return "memory"
        if "sstore" in function_name or "sload" in function_name:
            return "storage"
        return "call"

    def apply_condition(self, domain: Domain, condition: Condition, branch_taken: bool) -> Domain:
        """Apply branch-specific narrowing based on a condition.

        Looks up the comparison info stored by ComparisonHandler and
        adds the condition (or its negation) as a path constraint.

        Args:
            domain: The current abstract state.
            condition: The condition operation from the branch.
            branch_taken: True if then-branch (condition is true),
                          False if else-branch (condition is false).

        Returns:
            Deep copy of domain with branch constraint as path constraint.
        """
        if not isinstance(domain, IntervalDomain):
            return domain

        filtered_domain = domain.deep_copy()

        if filtered_domain.state is None:
            return filtered_domain

        condition_name = get_variable_name(condition.value)
        comparison_info = filtered_domain.state.get_comparison(condition_name)

        if comparison_info is None:
            logger.debug(
                "No comparison info for condition variable {name}",
                name=condition_name,
            )
            return filtered_domain

        if not self._apply_interval_refinements(
            filtered_domain.state,
            comparison_info,
            branch_taken,
        ):
            return IntervalDomain.bottom(filtered_domain.context_id)

        branch_constraint = self._create_branch_constraint(comparison_info.condition, branch_taken)
        operation_id = StaticOperationId.from_operation(condition, condition.node)
        provenance = FactProvenance(
            context_id=filtered_domain.context_id,
            origin_kind=FactOriginKind.CFG_EDGE,
            operation_id=operation_id,
        )
        branch_fact = Fact(
            fact_id=FactId(
                owner=FactOwnerKind.STATE_LOCAL,
                kind=FactKind.BRANCH_GUARD,
                provenance=provenance,
                semantic_key=("branch", "true" if branch_taken else "false"),
            ),
            formula=branch_constraint,
        )
        filtered_domain.state.add_branch_constraint(branch_fact)
        return filtered_domain

    @staticmethod
    def _apply_interval_refinements(
        state: State,
        comparison_info: ComparisonInfo,
        branch_taken: bool,
    ) -> bool:
        """Apply every non-relational restriction for the selected branch."""
        for refinement in comparison_info.refinements:
            reachable = refinement.true_reachable if branch_taken else refinement.false_reachable
            if not reachable:
                return False
            interval = refinement.true_interval if branch_taken else refinement.false_interval
            if not state.refine_variable(refinement.variable_name, interval):
                return False
        return True

    def _create_branch_constraint(self, condition_term: SMTTerm, branch_taken: bool) -> SMTTerm:
        """Create the path constraint for a branch."""
        if branch_taken:
            return condition_term
        return self._solver.Not(condition_term)

    def apply_loop_widening(self, context: LoopWideningContext) -> LoopWideningResult:
        """Widen only loop-carried SSA values using their abstract intervals."""
        current = self._concrete_interval_domain(context.current_input)
        if current is None:
            return LoopWideningResult(context.current_input)
        precise = self._precise_loop_result(context, current)
        if precise is not None:
            return precise
        previous = self._concrete_interval_domain(context.previous_output)
        if previous is None:
            return self._loop_result(context, current)
        widened = self._widen_loop_variables(context, current, previous)
        return self._loop_result(context, widened)

    @staticmethod
    def _concrete_interval_domain(domain: Domain | None) -> IntervalDomain | None:
        """Return a reachable interval state suitable for abstract widening."""
        if not isinstance(domain, IntervalDomain):
            return None
        if domain.variant is not DomainVariant.STATE or domain.state is None:
            return None
        return domain

    def _precise_loop_result(
        self,
        context: LoopWideningContext,
        current: IntervalDomain,
    ) -> LoopWideningResult | None:
        """Use bounded unrolling only for a statically certified progression."""
        progression = self._loop_metadata.progression_for(context.header_id)
        if progression is None or current.state is None:
            return None
        maximum = progression.maximum_iterations(current.state)
        if maximum is None or maximum > PRECISE_LOOP_GENERATION_LIMIT:
            return None
        if progression.exhaustively_unrolled(context):
            return LoopWideningResult(context.previous_input.deep_copy())
        return self._loop_result(context, current)

    def _widen_loop_variables(
        self,
        context: LoopWideningContext,
        current: IntervalDomain,
        previous: IntervalDomain,
    ) -> IntervalDomain:
        """Apply threshold widening to only statically bound back-edge values."""
        if current.state is None or previous.state is None:
            raise ValueError("Loop widening requires concrete current and previous states")
        widened = current.state.deep_copy()
        for binding in context.variables:
            previous_value = previous.state.get_variable(binding.header_name)
            if previous_value is None:
                continue
            for name in binding.back_names:
                candidate = current.state.get_variable(name)
                if candidate is None:
                    continue
                interval = self._widened_interval(candidate, previous_value)
                widened.set_variable(name, candidate.with_interval(interval))
        return IntervalDomain.with_state(widened)

    def _widened_interval(
        self,
        current: TrackedSMTVariable,
        previous: TrackedSMTVariable,
    ) -> NumericInterval:
        """Widen growing bounds to the nearest literal or type threshold."""
        current_interval = current.interval
        previous_interval = previous.interval
        type_interval = current.type_interval
        thresholds = sorted(
            {
                type_interval.lower,
                type_interval.upper,
                *(
                    value
                    for value in self._thresholds
                    if type_interval.lower <= value <= type_interval.upper
                ),
            }
        )
        lower = current_interval.lower
        upper = current_interval.upper
        if lower < previous_interval.lower:
            lower = max(value for value in thresholds if value <= lower)
        if upper > previous_interval.upper:
            upper = min(value for value in thresholds if value >= upper)
        return NumericInterval(lower, upper)

    def _loop_result(
        self,
        context: LoopWideningContext,
        domain: IntervalDomain,
    ) -> LoopWideningResult:
        """Attach replaceable generation facts to one widened abstract state."""
        if domain.state is None:
            return LoopWideningResult(domain)
        facts: list[Fact[object]] = []
        for binding in context.variables:
            for name in binding.back_names:
                variable = domain.state.get_variable(name)
                if variable is None or variable.interval == variable.type_interval:
                    continue
                interval = variable.interval
                facts.append(
                    Fact(
                        fact_id=FactId(
                            owner=FactOwnerKind.LOOP_GENERATION,
                            kind=FactKind.RANGE_BOUND,
                            provenance=FactProvenance(
                                context_id=domain.context_id,
                                origin_kind=FactOriginKind.LOOP,
                                loop_header_id=context.header_id,
                                loop_generation=context.generation,
                            ),
                            semantic_key=(
                                "abstract_loop_range",
                                name,
                                str(interval.lower),
                                str(interval.upper),
                            ),
                        ),
                        formula=interval,
                    )
                )
        return LoopWideningResult(domain, tuple(facts))
