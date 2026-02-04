"""Interval analysis implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
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
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.analyses.data_flow.smt_solver.types import RangeSolveStatus
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

    # Default timeout for SMT queries (milliseconds)
    DEFAULT_TIMEOUT_MS = 1000

    def __init__(self, solver: SMTSolver, timeout_ms: int | None = None) -> None:
        self._direction: Direction = Forward()
        self._solver: SMTSolver = solver
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self._solver)
        self._thresholds: List[int] = []
        self._timeout_ms: int = timeout_ms if timeout_ms is not None else self.DEFAULT_TIMEOUT_MS

    @property
    def solver(self) -> SMTSolver:
        return self._solver

    def domain(self) -> Domain:
        return IntervalDomain.with_state(State({}))

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom()

    def prepare_for_function(self, function: Function) -> None:
        """Collect numeric literals from function for threshold widening."""
        self._thresholds = self._collect_thresholds(function)
        logger.debug(
            "Collected {count} thresholds for {name}: {thresholds}",
            count=len(self._thresholds),
            name=function.name,
            thresholds=self._thresholds[:20],
        )

    def _collect_thresholds(self, function: Function) -> List[int]:
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

    def _extract_constants_from_node(
        self, node: Node, threshold_set: set[int]
    ) -> None:
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
    def thresholds(self) -> List[int]:
        """Return the sorted list of widening thresholds."""
        return self._thresholds

    def transfer_function(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
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
        domain.state = State({})

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

        self._initialize_variable_to_zero(variable_declaration, domain)

    def _is_uninitialized_declaration(
        self,
        node: Node,
        variable: "LocalVariable",
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
        variable: "LocalVariable",
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
        )

        zero_term = self._solver.create_constant(0, sort)
        self._solver.assert_constraint(tracked.term == zero_term)

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

        from slither.slithir.operations.binary import Binary
        from slither.slithir.operations.unary import Unary
        from slither.slithir.operations.solidity_call import SolidityCall
        from slither.slithir.operations.high_level_call import HighLevelCall
        from slither.slithir.operations.internal_call import InternalCall
        from slither.slithir.operations.library_call import LibraryCall
        from slither.slithir.operations import Assignment
        from slither.slithir.operations.condition import Condition

        op_type = type(operation)

        # Categorize by operation type
        if op_type == Binary:
            # Further categorize binary operations
            binary_op = operation
            op_type_enum = getattr(binary_op, "type", None)
            if op_type_enum is not None:
                op_name_str = str(op_type_enum.name) if hasattr(op_type_enum, "name") else ""
                if op_name_str in ("ADDITION", "SUBTRACTION", "MULTIPLICATION", "DIVISION",
                                   "MODULO", "POWER"):
                    telemetry.record_transfer_op("arithmetic", handled=True)
                elif op_name_str in ("LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL",
                                     "EQUAL", "NOT_EQUAL"):
                    telemetry.record_transfer_op("comparison", handled=True)
                elif op_name_str in ("AND", "OR", "LEFT_SHIFT", "RIGHT_SHIFT",
                                     "CARET", "OROR", "ANDAND"):
                    telemetry.record_transfer_op("bitwise", handled=True)
                else:
                    telemetry.record_transfer_op("arithmetic", handled=True)
            else:
                telemetry.record_transfer_op("arithmetic", handled=True)
        elif op_type == Unary:
            telemetry.record_transfer_op("arithmetic", handled=True)
        elif op_type == SolidityCall:
            # Check for memory/storage operations
            func_name = getattr(operation, "function", None)
            func_str = str(func_name) if func_name else ""
            if "mstore" in func_str or "mload" in func_str:
                telemetry.record_transfer_op("memory", handled=True)
            elif "sstore" in func_str or "sload" in func_str:
                telemetry.record_transfer_op("storage", handled=True)
            else:
                telemetry.record_transfer_op("call", handled=True)
        elif op_type in (HighLevelCall, InternalCall, LibraryCall):
            telemetry.record_transfer_op("call", handled=True)
        elif op_type == Assignment:
            telemetry.record_transfer_op("assignment", handled=True)
        elif op_type == Condition:
            telemetry.record_transfer_op("comparison", handled=True)
        else:
            # Phi, TypeConversion, etc.
            telemetry.record_transfer_op("assignment", handled=True)

    def apply_condition(
        self, domain: Domain, condition: Condition, branch_taken: bool
    ) -> Domain:
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

        branch_constraint = self._create_branch_constraint(
            comparison_info.condition, branch_taken
        )
        filtered_domain.state.add_path_constraint(branch_constraint)
        return filtered_domain

    def _create_branch_constraint(
        self, condition_term: "SMTTerm", branch_taken: bool
    ) -> "SMTTerm":
        """Create the path constraint for a branch."""
        if branch_taken:
            return condition_term
        return self._solver.Not(condition_term)

    def apply_widening(
        self, current_state: Domain, previous_state: Domain, widening_thresholds: set
    ) -> Domain:
        """Selective threshold widening for loop back edges.

        Only widens variables whose bounds actually grew between iterations.
        Stable variables (bounds unchanged) are preserved with original bounds.

        SSA names differ across iterations (result_2 vs result_3), so we match
        variables by base name (stripping the SSA suffix).

        Args:
            current_state: The state being propagated (from loop body).
            previous_state: The existing state at the loop header.
            widening_thresholds: Unused (thresholds stored on analysis).

        Returns:
            Widened state with selectively widened variables.
        """
        if not isinstance(current_state, IntervalDomain):
            return current_state

        if current_state.variant != DomainVariant.STATE or current_state.state is None:
            return current_state

        if not isinstance(previous_state, IntervalDomain):
            return current_state

        # First iteration (BOTTOM) - no widening needed
        if previous_state.variant == DomainVariant.BOTTOM:
            return current_state

        if previous_state.state is None:
            return current_state

        # Build base name -> variable mappings for both states
        previous_by_base = self._build_base_name_map(previous_state.state)

        widened_state = State()

        for variable_name in current_state.state.variable_names():
            current_variable = current_state.state.get_variable(variable_name)
            if current_variable is None:
                continue

            # Match by base name (strip SSA suffix)
            base_name = self._extract_base_name(variable_name)
            previous_variable = previous_by_base.get(base_name)

            if previous_variable is None:
                # New variable - keep as-is
                widened_state.set_variable(variable_name, current_variable)
                continue

            # Compare bounds to check if value grew
            if self._bounds_are_stable(current_variable, previous_variable, current_state):
                # Stable - keep current variable (preserves its constraints)
                widened_state.set_variable(variable_name, current_variable)
            else:
                # Grew - widen to unconstrained (full type range)
                # NOTE: We cannot add explicit bounds constraints because SMT
                # constraints are permanent. Asserting bounds makes exit branches
                # unreachable. Full widening to type range is sound but imprecise.
                widened_variable = self._create_unconstrained_variable(current_variable)
                widened_state.set_variable(variable_name, widened_variable)

        # Copy path constraints
        for constraint in current_state.state.get_path_constraints():
            widened_state.add_path_constraint(constraint)

        return IntervalDomain.with_state(widened_state)

    def _extract_base_name(self, ssa_name: str) -> str:
        """Extract base variable name from SSA name (strip _N suffix)."""
        # SSA names are like "result_3", "i_2", "TMP_5"
        # We want to extract "result", "i", "TMP"
        parts = ssa_name.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
        return ssa_name

    def _build_base_name_map(
        self, state: State
    ) -> dict[str, TrackedSMTVariable]:
        """Build mapping from base name to variable (latest SSA version)."""
        base_map: dict[str, TrackedSMTVariable] = {}
        for variable_name in state.variable_names():
            base_name = self._extract_base_name(variable_name)
            variable = state.get_variable(variable_name)
            if variable is not None:
                # If multiple SSA versions, keep any (they should have same bounds)
                base_map[base_name] = variable
        return base_map

    def _bounds_are_stable(
        self,
        current_variable: TrackedSMTVariable,
        previous_variable: TrackedSMTVariable,
        current_state: IntervalDomain,
    ) -> bool:
        """Check if current bounds are contained within previous bounds.

        Returns True if current ⊆ previous (no growth).
        """
        current_bounds = self._query_variable_bounds(current_variable, current_state)
        previous_bounds = self._query_variable_bounds(previous_variable, current_state)

        if current_bounds is None or previous_bounds is None:
            return False  # Unknown - assume unstable

        current_min, current_max = current_bounds
        previous_min, previous_max = previous_bounds

        # Stable if current is contained within previous
        return current_min >= previous_min and current_max <= previous_max

    def _query_variable_bounds(
        self,
        variable: TrackedSMTVariable,
        domain: IntervalDomain,
    ) -> tuple[int, int] | None:
        """Query min/max bounds for a variable using SMT solver."""
        if domain.state is None:
            return None

        extra_constraints = list(domain.state.get_path_constraints())

        status, min_value, max_value = self._solver.solve_range(
            variable.term,
            extra_constraints=extra_constraints,
            timeout_ms=self._timeout_ms,
            signed=variable.base.metadata.get("is_signed", False),
        )

        if status != RangeSolveStatus.SUCCESS:
            return None

        return (min_value, max_value)

    def _widen_variable_to_threshold(
        self,
        current_variable: TrackedSMTVariable,
        previous_variable: TrackedSMTVariable,
        current_state: IntervalDomain,
    ) -> TrackedSMTVariable:
        """Create new variable with bounds widened to next threshold."""
        current_bounds = self._query_variable_bounds(current_variable, current_state)
        previous_bounds = self._query_variable_bounds(previous_variable, current_state)

        if current_bounds is None or previous_bounds is None:
            return self._create_unconstrained_variable(current_variable)

        widened_min, widened_max = self._compute_widened_bounds(
            current_bounds, previous_bounds
        )

        return self._create_variable_with_bounds(
            current_variable, widened_min, widened_max
        )

    def _compute_widened_bounds(
        self,
        current_bounds: tuple[int, int],
        previous_bounds: tuple[int, int],
    ) -> tuple[int, int]:
        """Compute widened bounds using threshold list."""
        current_min, current_max = current_bounds
        previous_min, previous_max = previous_bounds

        widened_min = current_min
        widened_max = current_max

        # If lower bound decreased, widen to next threshold below
        if current_min < previous_min:
            widened_min = self._next_threshold_below(current_min)

        # If upper bound increased, widen to next threshold above
        if current_max > previous_max:
            widened_max = self._next_threshold_above(current_max)

        return (widened_min, widened_max)

    def _next_threshold_below(self, value: int) -> int:
        """Find largest threshold ≤ value."""
        for threshold in reversed(self._thresholds):
            if threshold <= value:
                return threshold
        return self._thresholds[0] if self._thresholds else 0

    def _next_threshold_above(self, value: int) -> int:
        """Find smallest threshold ≥ value."""
        for threshold in self._thresholds:
            if threshold >= value:
                return threshold
        return self._thresholds[-1] if self._thresholds else (1 << 256) - 1

    def _create_unconstrained_variable(
        self, template: TrackedSMTVariable
    ) -> TrackedSMTVariable:
        """Create an unconstrained variable with same type as template."""
        is_signed = template.base.metadata.get("is_signed", False)
        bit_width = template.base.metadata.get("bit_width", 256)

        return TrackedSMTVariable.create(
            self._solver,
            template.name,
            template.sort,
            is_signed=is_signed,
            bit_width=bit_width,
        )

    def _create_variable_with_bounds(
        self,
        template: TrackedSMTVariable,
        lower_bound: int,
        upper_bound: int,
    ) -> TrackedSMTVariable:
        """Create a variable constrained to [lower_bound, upper_bound]."""
        is_signed = template.base.metadata.get("is_signed", False)
        bit_width = template.base.metadata.get("bit_width", 256)

        new_variable = TrackedSMTVariable.create(
            self._solver,
            template.name,
            template.sort,
            is_signed=is_signed,
            bit_width=bit_width,
        )

        # Add bounds constraints
        lower_term = self._solver.create_constant(lower_bound, template.sort)
        upper_term = self._solver.create_constant(upper_bound, template.sort)

        if is_signed:
            lower_constraint = self._solver.bv_sge(new_variable.term, lower_term)
            upper_constraint = self._solver.bv_sle(new_variable.term, upper_term)
        else:
            lower_constraint = self._solver.bv_uge(new_variable.term, lower_term)
            upper_constraint = self._solver.bv_ule(new_variable.term, upper_term)

        self._solver.assert_constraint(lower_constraint)
        self._solver.assert_constraint(upper_constraint)

        return new_variable
