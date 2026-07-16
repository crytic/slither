"""Tests for complete, order-independent interval-state joins."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import pytest

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import ComparisonInfo, State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.engine.analysis import Analysis, AnalysisState
from slither.analyses.data_flow.engine.direction import Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver import Z3Solver
from slither.analyses.data_flow.smt_solver.facts import (
    AnalysisContextId,
    EncodingId,
    Fact,
    FactId,
    FactKind,
    FactOriginKind,
    FactOwnerKind,
    FactProvenance,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.query import QueryPurpose
from slither.analyses.data_flow.smt_solver.telemetry import (
    disable_telemetry,
    enable_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.core.cfg.node import NodeType
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation


ENCODING_ID = EncodingId("state_join.sol", "C.f()")
CONTEXT_ID = AnalysisContextId(ENCODING_ID)


def _solver() -> Z3Solver:
    solver = Z3Solver()
    solver.bind_function_encoding(ENCODING_ID)
    return solver


def _tracked(
    solver: Z3Solver,
    name: str,
    lower: int,
    upper: int,
    *,
    signed: bool = False,
    total: bool = True,
) -> TrackedSMTVariable:
    variable = TrackedSMTVariable.create(
        solver,
        name,
        Sort(SortKind.BITVEC, [8]),
        is_signed=signed,
        bit_width=8,
    )
    return variable.with_interval(NumericInterval(lower, upper), is_total=total)


def _operation(node_id: int, position: int = 0) -> StaticOperationId:
    return StaticOperationId(ENCODING_ID, node_id, position)


def _fact(formula: object, role: str, node_id: int) -> Fact:
    return Fact(
        fact_id=FactId(
            owner=FactOwnerKind.STATE_LOCAL,
            kind=FactKind.PATH_CONDITION,
            provenance=FactProvenance(
                context_id=CONTEXT_ID,
                origin_kind=FactOriginKind.CFG_EDGE,
                operation_id=_operation(node_id),
            ),
            semantic_key=(role,),
        ),
        formula=formula,
    )


def _owned_fact(
    formula: object,
    role: str,
    node_id: int,
    kind: FactKind,
) -> Fact:
    fact = _fact(formula, role, node_id)
    return Fact(
        fact_id=FactId(
            owner=fact.fact_id.owner,
            kind=kind,
            provenance=fact.fact_id.provenance,
            semantic_key=fact.fact_id.semantic_key,
        ),
        formula=formula,
    )


def _joined(left: State, right: State) -> State:
    domain = IntervalDomain.with_state(left.deep_copy())
    domain.join(IntervalDomain.with_state(right.deep_copy()))
    assert domain.variant is DomainVariant.STATE
    assert domain.state is not None
    return domain.state


def test_join_is_order_independent_across_complete_state() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 10)
    condition = x.term != 0
    common = _fact(condition, "common", 1)
    left_only = _fact(x.term < 5, "left", 2)
    right_only = _fact(x.term > 20, "right", 3)
    comparison = ComparisonInfo(condition, _operation(4))

    left = State(
        {"x": x},
        {"condition": comparison},
        facts=(common, left_only),
        dependencies={"x": {"left_source"}},
        storage_slots={"0": ["left_write"]},
        context_id=CONTEXT_ID,
    )
    right = State(
        {"x": _tracked(solver, "x", 20, 30)},
        {"condition": comparison},
        facts=(right_only, common),
        dependencies={"x": {"right_source"}},
        storage_slots={"0": ["right_write"]},
        context_id=CONTEXT_ID,
    )

    left_right = _joined(left, right)
    right_left = _joined(right, left)

    assert left_right.semantic_id() == right_left.semantic_id()
    assert left_right.get_variable("x").interval == NumericInterval(0, 30)
    assert left_right.get_explicit_fact_ids() == frozenset({common.fact_id})
    assert left_right.get_dependencies("x") == {"left_source", "right_source"}
    assert left_right.get_storage_writes("0") == ["left_write", "right_write"]
    assert not left_right.storage_may_be_unwritten("0")
    assert left_right.get_comparison("condition") == comparison
    assert left_right.get_facts() == right_left.get_facts()


def test_join_is_idempotent_without_new_semantics() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 5, 7)
    fact = _fact(x.term >= 5, "lower", 1)
    state = State(
        {"x": x},
        facts=(fact,),
        dependencies={"x": {"input"}},
        storage_slots={"0": ["write"]},
        context_id=CONTEXT_ID,
    )

    joined = _joined(state, state)

    assert joined.semantic_id() == state.semantic_id()
    assert joined.get_facts() == state.get_facts()


def test_join_is_associative_for_intervals_facts_storage_and_dependencies() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 5)
    common = _fact(x.term >= 0, "common", 1)
    states = [
        State(
            {"x": _tracked(solver, "x", lower, upper)},
            facts=(common, _fact(x.term != index, f"exclusive_{index}", 10 + index)),
            dependencies={"x": {f"source_{index}"}},
            storage_slots={"0": [f"write_{index}"]},
            context_id=CONTEXT_ID,
        )
        for index, (lower, upper) in enumerate(((0, 5), (10, 15), (20, 25)))
    ]

    left_grouped = _joined(_joined(states[0], states[1]), states[2])
    right_grouped = _joined(states[0], _joined(states[1], states[2]))

    assert left_grouped.semantic_id() == right_grouped.semantic_id()
    assert left_grouped.get_variable("x").interval == NumericInterval(0, 25)
    assert left_grouped.get_explicit_fact_ids() == frozenset({common.fact_id})


def test_bottom_is_join_identity_and_top_is_absorbing() -> None:
    solver = _solver()
    state_domain = IntervalDomain.with_state(
        State({"x": _tracked(solver, "x", 5, 7)}, context_id=CONTEXT_ID)
    )

    left_bottom = IntervalDomain.bottom(CONTEXT_ID)
    assert left_bottom.join(state_domain)
    assert left_bottom.semantic_id() == state_domain.semantic_id()

    right_bottom = state_domain.deep_copy()
    assert not right_bottom.join(IntervalDomain.bottom(CONTEXT_ID))
    assert right_bottom.semantic_id() == state_domain.semantic_id()

    both_bottom = IntervalDomain.bottom(CONTEXT_ID)
    assert not both_bottom.join(IntervalDomain.bottom(CONTEXT_ID))
    assert both_bottom.variant is DomainVariant.BOTTOM

    transient_bottom = IntervalDomain(DomainVariant.BOTTOM, state_domain.state.deep_copy())
    assert transient_bottom.semantic_id() == IntervalDomain.bottom(CONTEXT_ID).semantic_id()

    top = IntervalDomain.top(CONTEXT_ID)
    assert top.semantic_id() == _join_domain(top, state_domain).semantic_id()


def _join_domain(left: IntervalDomain, right: IntervalDomain) -> IntervalDomain:
    result = left.deep_copy()
    result.join(right)
    return result


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ((0, 10), (20, 30), (0, 30)),
        ((0, 10), (5, 7), (0, 10)),
        ((0, 255), (5, 7), (0, 255)),
        ((-128, -10), (5, 20), (-128, 20)),
    ],
)
def test_variable_intervals_use_hulls(
    left: tuple[int, int],
    right: tuple[int, int],
    expected: tuple[int, int],
) -> None:
    solver = _solver()
    signed = expected[0] < 0
    first = State(
        {"x": _tracked(solver, "x", *left, signed=signed)},
        context_id=CONTEXT_ID,
    )
    second = State(
        {"x": _tracked(solver, "x", *right, signed=signed)},
        context_id=CONTEXT_ID,
    )

    joined = _joined(first, second)

    assert joined.get_variable("x").interval == NumericInterval(*expected)


def test_missing_variable_is_path_optional_not_blindly_copied() -> None:
    solver = _solver()
    present = State({"x": _tracked(solver, "x", 5, 7)}, context_id=CONTEXT_ID)
    absent = State(context_id=CONTEXT_ID)

    joined = _joined(present, absent)
    reversed_join = _joined(absent, present)
    variable = joined.get_variable("x")

    assert variable is not None
    assert not variable.is_total
    assert variable.interval == NumericInterval(5, 7)
    assert joined.semantic_id() == reversed_join.semantic_id()
    assert all(fact.fact_id.kind is not FactKind.RANGE_BOUND for fact in joined.get_facts())


def test_storage_missing_from_one_path_remains_possibly_unwritten() -> None:
    solver = _solver()
    written = State(
        {"value": _tracked(solver, "value", 42, 42)},
        storage_slots={"0": ["value"]},
        context_id=CONTEXT_ID,
    )
    unwritten = State(context_id=CONTEXT_ID)

    joined = _joined(written, unwritten)

    assert joined.get_storage_writes("0") == ["value"]
    assert joined.storage_may_be_unwritten("0")


def test_comparisons_intersect_and_dependencies_union() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 255)
    common = ComparisonInfo(x.term < 10, _operation(1))
    structurally_equal_but_distinct = ComparisonInfo(x.term < 10, _operation(2))
    left = State(
        {"x": x},
        {"common": common, "exclusive": common},
        dependencies={"x": {"a"}},
        context_id=CONTEXT_ID,
    )
    right = State(
        {"x": x},
        {"common": common, "exclusive": structurally_equal_but_distinct},
        dependencies={"x": {"b"}},
        context_id=CONTEXT_ID,
    )

    joined = _joined(left, right)

    assert joined.get_comparison("common") == common
    assert joined.get_comparison("exclusive") is None
    assert joined.get_dependencies("x") == {"a", "b"}


def test_join_does_not_mutate_predecessors_or_alias_mutable_containers() -> None:
    solver = _solver()
    left = State(
        {"x": _tracked(solver, "x", 0, 10)},
        dependencies={"x": {"left"}},
        storage_slots={"0": ["left_write"]},
        context_id=CONTEXT_ID,
    )
    right = State(
        {"x": _tracked(solver, "x", 20, 30)},
        dependencies={"x": {"right"}},
        storage_slots={"0": ["right_write"]},
        context_id=CONTEXT_ID,
    )
    left_id = left.semantic_id()
    right_id = right.semantic_id()

    joined = _joined(left, right)
    joined.add_dependency("x", "joined_only")
    joined.add_storage_write("0", "joined_write")

    assert left.semantic_id() == left_id
    assert right.semantic_id() == right_id
    assert "joined_only" not in left.get_dependencies("x")
    assert "joined_write" not in right.get_storage_writes("0")


def test_joined_state_materializes_exactly_in_query_session() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 10)
    common = _fact(x.term >= 0, "common", 1)
    left = State(
        {"x": x},
        facts=(common, _fact(x.term < 5, "left", 2)),
        context_id=CONTEXT_ID,
    )
    right = State(
        {"x": _tracked(solver, "x", 20, 30)},
        facts=(common, _fact(x.term > 20, "right", 3)),
        context_id=CONTEXT_ID,
    )
    joined = _joined(left, right)
    before = joined.semantic_id()

    session = solver.create_query_session(
        purpose=QueryPurpose.FEASIBILITY,
        timeout_ms=100,
        state_id=before,
        state_facts=joined.get_facts(),
    )
    try:
        materialized_ids = frozenset(
            fact.fact_id for fact in session.materialization.state_facts
        )
        assert materialized_ids == before.active_fact_ids
        assert materialized_ids == joined.get_fact_ids()
        assert joined.get_explicit_fact_ids() == frozenset({common.fact_id})
    finally:
        diagnostics = session.close()

    assert diagnostics.cleanup_balanced
    assert solver.active_query_sessions == 0
    assert joined.semantic_id() == before


def test_branch_arithmetic_join_is_conservative_in_both_orders() -> None:
    solver = _solver()
    uint_max = (1 << 256) - 1
    uint_sort = Sort(SortKind.BITVEC, [256])
    x = TrackedSMTVariable.create(solver, "x", uint_sort, bit_width=256)
    y = TrackedSMTVariable.create(solver, "y", uint_sort, bit_width=256)
    true_x = x.with_interval(NumericInterval(0, 49))
    false_x = x.with_interval(NumericInterval(50, uint_max))
    true_y = y.with_interval(NumericInterval(10, 59))
    false_y = y.with_interval(NumericInterval(40, uint_max - 10))
    true_guard = _owned_fact(x.term < 50, "true_guard", 1, FactKind.BRANCH_GUARD)
    false_guard = _owned_fact(x.term >= 50, "false_guard", 1, FactKind.BRANCH_GUARD)
    add_success = _owned_fact(y.term >= x.term, "checked_add", 2, FactKind.CHECKED_ARITHMETIC)
    sub_success = _owned_fact(y.term <= x.term, "checked_sub", 3, FactKind.CHECKED_ARITHMETIC)
    true_state = State(
        {"x": true_x, "y": true_y},
        facts=(true_guard, add_success),
        context_id=CONTEXT_ID,
    )
    false_state = State(
        {"x": false_x, "y": false_y},
        facts=(false_guard, sub_success),
        context_id=CONTEXT_ID,
    )

    joined = _joined(true_state, false_state)
    reversed_join = _joined(false_state, true_state)

    assert joined.semantic_id() == reversed_join.semantic_id()
    assert joined.get_variable("x").interval == NumericInterval(0, uint_max)
    assert joined.get_variable("y").interval == NumericInterval(10, uint_max - 10)
    assert joined.get_explicit_fact_ids() == frozenset()
    before_query = joined.semantic_id()
    result = solver.solve_range_result(
        y.term,
        state_id=joined.semantic_id(),
        state_facts=joined.get_facts(),
        timeout_ms=1_000,
    )
    assert (result.lower, result.upper) == (10, uint_max - 10)
    assert result.diagnostics.cleanup_balanced
    assert solver.active_query_sessions == 0
    assert joined.semantic_id() == before_query


def test_join_rejects_incompatible_contexts() -> None:
    solver = _solver()
    left = State({"x": _tracked(solver, "x", 0, 10)}, context_id=CONTEXT_ID)
    other_context = AnalysisContextId(EncodingId("state_join.sol", "C.g()"))
    right = State({"x": _tracked(solver, "x", 20, 30)}, context_id=other_context)

    with pytest.raises(ValueError, match="analysis contexts"):
        _joined(left, right)

    with pytest.raises(ValueError, match="analysis contexts"):
        IntervalDomain.bottom(CONTEXT_ID).join(IntervalDomain.bottom(other_context))

    with pytest.raises(ValueError, match="analysis contexts"):
        IntervalDomain.with_state(left).join(IntervalDomain.bottom(other_context))


def test_structurally_equal_facts_with_distinct_ids_do_not_become_common() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 255)
    formula = x.term < 10
    left = State(
        {"x": x},
        facts=(_fact(formula, "left", 1),),
        context_id=CONTEXT_ID,
    )
    right = State(
        {"x": x},
        facts=(_fact(formula, "right", 2),),
        context_id=CONTEXT_ID,
    )

    assert _joined(left, right).get_explicit_fact_ids() == frozenset()


def test_join_change_detection_covers_every_mutable_state_component() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 5, 7)
    fact = _fact(x.term >= 5, "common", 1)
    comparison = ComparisonInfo(x.term < 10, _operation(2))
    cases = [
        (
            State({"x": x}, context_id=CONTEXT_ID),
            State({"x": _tracked(solver, "x", 0, 10)}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, facts=(fact,), context_id=CONTEXT_ID),
            State({"x": x}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, storage_slots={"0": ["a"]}, context_id=CONTEXT_ID),
            State({"x": x}, storage_slots={"0": ["b"]}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, {"condition": comparison}, context_id=CONTEXT_ID),
            State({"x": x}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, dependencies={"x": {"a"}}, context_id=CONTEXT_ID),
            State({"x": x}, dependencies={"x": {"b"}}, context_id=CONTEXT_ID),
        ),
    ]

    for left, right in cases:
        domain = IntervalDomain.with_state(left)
        assert domain.join(IntervalDomain.with_state(right))


def test_semantic_identity_includes_overflow_operation_metadata() -> None:
    solver = _solver()
    variable = _tracked(solver, "x", 0, 10)
    predicate = variable.term < 255
    first = variable.with_overflow_predicates(
        no_overflow=predicate,
        operation_id=_operation(1),
    )
    second = variable.with_overflow_predicates(
        no_overflow=predicate,
        operation_id=_operation(2),
    )

    first_id = State({"x": first}, context_id=CONTEXT_ID).semantic_id()
    second_id = State({"x": second}, context_id=CONTEXT_ID).semantic_id()

    assert first_id != second_id


def test_join_telemetry_distinguishes_changes_and_semantic_noops() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = _solver()
    state = State({"x": _tracked(solver, "x", 5, 7)}, context_id=CONTEXT_ID)
    domain = IntervalDomain.with_state(state)

    try:
        assert not domain.join(IntervalDomain.with_state(state.deep_copy()))
        assert domain.join(
            IntervalDomain.with_state(
                State({"x": _tracked(solver, "x", 0, 10)}, context_id=CONTEXT_ID)
            )
        )
        metrics = telemetry.evaluation.state_joins
        assert metrics.attempted == 2
        assert metrics.changed == 1
        assert metrics.semantic_noops == 1
    finally:
        disable_telemetry()
        reset_telemetry()


@dataclass(eq=False)
class _TestNode:
    node_id: int
    type: NodeType = NodeType.EXPRESSION
    irs_ssa: list[Operation] | None = None
    sons: list[_TestNode] | None = None

    def __post_init__(self) -> None:
        if self.sons is None:
            self.sons = []


class _CountingAnalysis(Analysis):
    def __init__(self) -> None:
        self.transfers: dict[int, int] = {}
        self._direction = Forward()

    def domain(self) -> Domain:
        return IntervalDomain.with_state(State(context_id=CONTEXT_ID))

    def direction(self) -> Forward:
        return self._direction

    def transfer_function(
        self,
        node: _TestNode,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
        del operation
        self.transfers[node.node_id] = self.transfers.get(node.node_id, 0) + 1
        assert domain.state is not None
        domain.state.add_dependency("x", f"transfer_{node.node_id}")

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom(CONTEXT_ID)

    def apply_condition(
        self,
        domain: Domain,
        condition: Condition,
        branch_taken: bool,
    ) -> Domain:
        del condition, branch_taken
        return domain


class _NoopCountingAnalysis(_CountingAnalysis):
    def transfer_function(
        self,
        node: _TestNode,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
        del domain, operation
        self.transfers[node.node_id] = self.transfers.get(node.node_id, 0) + 1


def _assert_component_change_reruns_transfer(stored: State, incoming: State) -> None:
    source = _TestNode(1)
    target = _TestNode(2)
    source.sons = [target]
    global_state = {
        1: AnalysisState(
            IntervalDomain.with_state(incoming),
            IntervalDomain.bottom(CONTEXT_ID),
        ),
        2: AnalysisState(
            IntervalDomain.with_state(stored),
            IntervalDomain.bottom(CONTEXT_ID),
        ),
    }
    analysis = _NoopCountingAnalysis()
    worklist = deque()

    analysis.direction().apply_transfer_function(
        analysis,
        global_state[1],
        source,
        worklist,
        global_state,
    )
    assert list(worklist) == [target]

    analysis.direction().apply_transfer_function(
        analysis,
        global_state[2],
        worklist.popleft(),
        worklist,
        global_state,
    )
    assert analysis.transfers[2] == 1


def test_forward_reruns_for_each_semantic_component_change() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 5, 7)
    fact = _fact(x.term >= 5, "stored", 1)
    comparison = ComparisonInfo(x.term < 10, _operation(2))
    cases = [
        (
            State({"x": x}, context_id=CONTEXT_ID),
            State({"x": _tracked(solver, "x", 0, 10)}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, facts=(fact,), context_id=CONTEXT_ID),
            State({"x": x}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, storage_slots={"0": ["a"]}, context_id=CONTEXT_ID),
            State({"x": x}, storage_slots={"0": ["b"]}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, {"condition": comparison}, context_id=CONTEXT_ID),
            State({"x": x}, context_id=CONTEXT_ID),
        ),
        (
            State({"x": x}, dependencies={"x": {"a"}}, context_id=CONTEXT_ID),
            State({"x": x}, dependencies={"x": {"b"}}, context_id=CONTEXT_ID),
        ),
    ]

    for stored, incoming in cases:
        _assert_component_change_reruns_transfer(stored, incoming)


def test_forward_transfer_preserves_input_and_skips_unchanged_revisit() -> None:
    solver = _solver()
    x = _tracked(solver, "x", 0, 10)
    fact = _fact(x.term < 10, "initial", 1)
    source_state = State({"x": x}, facts=(fact,), context_id=CONTEXT_ID)
    source_input = IntervalDomain.with_state(source_state)
    source_before = source_input.semantic_id()
    target_input = IntervalDomain.bottom(CONTEXT_ID)
    source = _TestNode(1)
    target = _TestNode(2)
    source.sons = [target]
    global_state = {
        1: AnalysisState(source_input, IntervalDomain.bottom(CONTEXT_ID)),
        2: AnalysisState(target_input, IntervalDomain.bottom(CONTEXT_ID)),
    }
    analysis = _CountingAnalysis()
    worklist = deque()

    analysis.direction().apply_transfer_function(
        analysis,
        global_state[1],
        source,
        worklist,
        global_state,
    )

    assert source_input.semantic_id() == source_before
    assert global_state[1].post.semantic_id() != source_before
    assert list(worklist) == [target]

    queued = worklist.popleft()
    analysis.direction().apply_transfer_function(
        analysis,
        global_state[2],
        queued,
        worklist,
        global_state,
    )
    assert analysis.transfers[2] == 1

    analysis.direction().apply_transfer_function(
        analysis,
        global_state[1],
        source,
        worklist,
        global_state,
    )
    assert list(worklist) == []
    assert analysis.transfers[2] == 1

    changed_source = IntervalDomain.with_state(State({"x": x}, context_id=CONTEXT_ID))
    global_state[1].pre = changed_source
    analysis.direction().apply_transfer_function(
        analysis,
        global_state[1],
        source,
        worklist,
        global_state,
    )
    assert list(worklist) == [target]

    analysis.direction().apply_transfer_function(
        analysis,
        global_state[2],
        worklist.popleft(),
        worklist,
        global_state,
    )
    assert analysis.transfers[2] == 2
