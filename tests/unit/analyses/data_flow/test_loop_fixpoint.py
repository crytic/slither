"""Tests for dominator-defined loop fixpoints and generation ownership."""

from __future__ import annotations

from dataclasses import dataclass, field

from slither.analyses.data_flow.analyses.interval.analysis.analysis import (
    IntervalAnalysis,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import ComparisonInfo, State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.loop import (
    ControlFlowEdgeId,
    LoopHeaderFixpoint,
    LoopStructure,
    LoopVariableId,
    LoopWideningContext,
    LoopWideningResult,
)
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
    LoopHeaderId,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind


ENCODING_ID = EncodingId("loop_fixpoint.sol", "C.f()")
CONTEXT_ID = AnalysisContextId(ENCODING_ID)
HEADER_ID = LoopHeaderId(ENCODING_ID, 2)


@dataclass
class _Filename:
    relative: str = "loop_fixpoint.sol"


@dataclass
class _SourceMapping:
    filename: _Filename = field(default_factory=_Filename)


@dataclass
class _FunctionStub:
    canonical_name: str = "C.f()"
    source_mapping: _SourceMapping = field(default_factory=_SourceMapping)
    nodes: list[_NodeStub] = field(default_factory=list)


@dataclass(eq=False)
class _NodeStub:
    node_id: int
    function: _FunctionStub
    sons: list[_NodeStub] = field(default_factory=list)
    fathers: list[_NodeStub] = field(default_factory=list)
    dominators: set[_NodeStub] = field(default_factory=set)


def _loop_cfg() -> tuple[_FunctionStub, dict[int, _NodeStub]]:
    function = _FunctionStub()
    nodes = {node_id: _NodeStub(node_id, function) for node_id in range(1, 6)}
    edges = ((1, 2), (2, 3), (2, 5), (3, 4), (4, 2))
    for source_id, destination_id in edges:
        source = nodes[source_id]
        destination = nodes[destination_id]
        source.sons.append(destination)
        destination.fathers.append(source)
    nodes[1].dominators = {nodes[1]}
    nodes[2].dominators = {nodes[1], nodes[2]}
    nodes[3].dominators = {nodes[1], nodes[2], nodes[3]}
    nodes[4].dominators = {nodes[1], nodes[2], nodes[3], nodes[4]}
    nodes[5].dominators = {nodes[1], nodes[2], nodes[5]}
    function.nodes = list(nodes.values())
    return function, nodes


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
    total: bool = True,
) -> TrackedSMTVariable:
    variable = TrackedSMTVariable.create(
        solver,
        name,
        Sort(SortKind.BITVEC, [8]),
        bit_width=8,
    )
    return variable.with_interval(NumericInterval(lower, upper), is_total=total)


def _domain(solver: Z3Solver, lower: int, upper: int) -> IntervalDomain:
    return IntervalDomain.with_state(
        State({"x": _tracked(solver, "x", lower, upper)}, context_id=CONTEXT_ID)
    )


class _RecordingAnalysis(Analysis):
    def __init__(self) -> None:
        self.contexts: list[LoopWideningContext] = []
        self._direction = Forward()

    def domain(self) -> Domain:
        return IntervalDomain.with_state(State(context_id=CONTEXT_ID))

    def direction(self) -> Direction:
        return self._direction

    def transfer_function(self, node: object, domain: Domain, operation: object) -> None:
        return None

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom(CONTEXT_ID)

    def apply_loop_widening(self, context: LoopWideningContext) -> LoopWideningResult:
        self.contexts.append(context)
        fact = Fact(
            fact_id=FactId(
                owner=FactOwnerKind.LOOP_GENERATION,
                kind=FactKind.RANGE_BOUND,
                provenance=FactProvenance(
                    context_id=CONTEXT_ID,
                    origin_kind=FactOriginKind.LOOP,
                    loop_header_id=context.header_id,
                    loop_generation=context.generation,
                ),
                semantic_key=("generation", str(context.generation)),
            ),
            formula=context.generation,
        )
        return LoopWideningResult(context.current_input, (fact,))


def test_natural_loop_classification_excludes_preheader_and_is_stable() -> None:
    function, nodes = _loop_cfg()
    first = LoopStructure.from_function(function)
    function.nodes.reverse()
    second = LoopStructure.from_function(function)
    preheader = ControlFlowEdgeId(1, 2)
    back_edge = ControlFlowEdgeId(4, 2)

    assert not first.is_back_edge(preheader)
    assert first.is_back_edge(back_edge)
    assert first.loops == second.loops
    assert first.loops[0].entry_edges == frozenset({preheader})
    assert first.loops[0].back_edges == frozenset({back_edge})
    assert first.loops[0].header_id == LoopHeaderId.from_node(nodes[2])
    assert LoopHeaderId.from_node(nodes[2]) == LoopHeaderId.from_node(nodes[2])


def test_generation_advances_only_for_changed_header_approximation() -> None:
    solver = _solver()
    analysis = _RecordingAnalysis()
    tracker = LoopHeaderFixpoint(HEADER_ID, ())
    entry = ControlFlowEdgeId(1, 2)
    back = ControlFlowEdgeId(4, 2)

    assert tracker.update(entry, _domain(solver, 0, 0), False, analysis).changed
    tracker.record_output(_domain(solver, 0, 0))
    assert tracker.update(back, _domain(solver, 1, 1), True, analysis).changed
    assert tracker.generation == 1
    assert not tracker.update(back, _domain(solver, 1, 1), True, analysis).changed
    assert tracker.generation == 1
    assert len(analysis.contexts) == 1


def test_widening_context_keeps_previous_and_current_semantic_states_separate() -> None:
    solver = _solver()
    analysis = _RecordingAnalysis()
    tracker = LoopHeaderFixpoint(HEADER_ID, ())
    entry_state = _domain(solver, 0, 0)
    output_state = _domain(solver, 0, 1)

    tracker.update(ControlFlowEdgeId(1, 2), entry_state, False, analysis)
    tracker.record_output(output_state)
    tracker.update(ControlFlowEdgeId(4, 2), _domain(solver, 2, 3), True, analysis)
    context = analysis.contexts[0]

    assert context.previous_input.semantic_id() == entry_state.semantic_id()
    assert context.current_input.semantic_id() != context.previous_input.semantic_id()
    assert context.previous_output is not None
    assert context.previous_output.semantic_id() == output_state.semantic_id()
    assert context.previous_input is not context.current_input


def test_generation_facts_replace_obsolete_generation() -> None:
    solver = _solver()
    analysis = _RecordingAnalysis()
    tracker = LoopHeaderFixpoint(HEADER_ID, ())
    entry = ControlFlowEdgeId(1, 2)
    back = ControlFlowEdgeId(4, 2)

    tracker.update(entry, _domain(solver, 0, 0), False, analysis)
    tracker.record_output(_domain(solver, 0, 0))
    tracker.update(back, _domain(solver, 1, 1), True, analysis)
    first_ids = tracker.generation_fact_ids
    tracker.record_output(_domain(solver, 0, 1))
    tracker.update(back, _domain(solver, 1, 2), True, analysis)

    assert tracker.generation == 2
    assert first_ids.isdisjoint(tracker.generation_fact_ids)
    assert {fact.fact_id.provenance.loop_generation for fact in tracker.generation_facts} == {2}


def _run_multiple_back_edges(order: tuple[ControlFlowEdgeId, ...]) -> IntervalDomain:
    solver = _solver()
    analysis = _RecordingAnalysis()
    tracker = LoopHeaderFixpoint(HEADER_ID, ())
    states = {
        ControlFlowEdgeId(4, 2): _domain(solver, 1, 5),
        ControlFlowEdgeId(5, 2): _domain(solver, 10, 20),
    }
    tracker.update(ControlFlowEdgeId(1, 2), _domain(solver, 0, 0), False, analysis)
    tracker.record_output(_domain(solver, 0, 0))
    for edge in order:
        tracker.update(edge, states[edge], True, analysis)
    assert isinstance(tracker.current_input, IntervalDomain)
    assert tracker.generation == 1
    return tracker.current_input


def test_multiple_back_edges_join_independently_of_arrival_order() -> None:
    first = ControlFlowEdgeId(4, 2)
    second = ControlFlowEdgeId(5, 2)
    left = _run_multiple_back_edges((first, second))
    right = _run_multiple_back_edges((second, first))

    assert left.semantic_id() == right.semantic_id()
    assert left.state is not None
    assert left.state.get_variable("x").interval == NumericInterval(0, 20)


def test_interval_widening_preserves_complete_state_and_solver_ownership() -> None:
    solver = _solver()
    analysis = IntervalAnalysis(solver, timeout_ms=10)
    entry = _tracked(solver, "x_entry", 0, 0)
    back = _tracked(solver, "x_back", 1, 5, total=False)
    marker = _tracked(solver, "marker", 7, 7)
    operation_id = StaticOperationId(ENCODING_ID, 9, 0)
    comparison = ComparisonInfo(back.term < 10, operation_id)
    fact = Fact(
        fact_id=FactId(
            owner=FactOwnerKind.STATE_LOCAL,
            kind=FactKind.PATH_CONDITION,
            provenance=FactProvenance(
                context_id=CONTEXT_ID,
                origin_kind=FactOriginKind.CFG_EDGE,
                operation_id=operation_id,
            ),
            semantic_key=("preserved",),
        ),
        formula=back.term != 0,
    )
    current = IntervalDomain.with_state(
        State(
            {"x_entry": entry, "x_back": back, "marker": marker},
            {"condition": comparison},
            facts=(fact,),
            dependencies={"x_back": {"source"}},
            storage_slots={"0": ["marker"]},
            context_id=CONTEXT_ID,
        )
    )
    previous_output = IntervalDomain.with_state(
        State({"x_phi": _tracked(solver, "x_phi", 0, 0)}, context_id=CONTEXT_ID)
    )
    context = LoopWideningContext(
        HEADER_ID,
        1,
        _domain(solver, 0, 0),
        current,
        previous_output,
        (LoopVariableId("x_phi", ("x_entry",), ("x_back",)),),
    )
    encoding_before = solver.function_encoding.fact_ids()

    result = analysis.apply_loop_widening(context)

    assert isinstance(result.state, IntervalDomain)
    assert result.state.variant is DomainVariant.STATE
    assert result.state.state is not None
    widened = result.state.state
    assert widened.get_variable("x_back").interval == NumericInterval(1, 255)
    assert not widened.get_variable("x_back").is_total
    assert widened.get_variable("marker").interval == NumericInterval(7, 7)
    assert widened.get_dependencies("x_back") == {"source"}
    assert widened.get_storage_writes("0") == ["marker"]
    assert not widened.storage_may_be_unwritten("0")
    assert widened.get_comparison("condition") == comparison
    assert widened.get_explicit_fact_ids() == frozenset({fact.fact_id})
    assert widened.context_id == CONTEXT_ID
    assert result.generation_facts
    assert all(
        fact.fact_id.owner is FactOwnerKind.LOOP_GENERATION for fact in result.generation_facts
    )
    assert all(fact.fact_id not in widened.get_fact_ids() for fact in result.generation_facts)
    assert solver.function_encoding.fact_ids() == encoding_before
    assert solver.active_query_sessions == 0
