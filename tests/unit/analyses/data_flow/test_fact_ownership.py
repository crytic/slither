"""Tests for semantic fact ownership and state identity."""

from dataclasses import dataclass

import pytest

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.interprocedural import (
    build_call_symbol_prefix,
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
    StaticOperationId,
    make_query_fact,
)
from slither.analyses.data_flow.smt_solver.telemetry import (
    disable_telemetry,
    enable_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind


def _context(function: str = "C.f()") -> AnalysisContextId:
    return AnalysisContextId(EncodingId("test.sol", function))


def _operation(
    function: str = "C.f()",
    node_id: int = 1,
    position: int = 0,
) -> StaticOperationId:
    return StaticOperationId(EncodingId("test.sol", function), node_id, position)


def _fact(
    formula: object,
    *,
    owner: FactOwnerKind = FactOwnerKind.IMMUTABLE_EQUATION,
    origin: FactOriginKind = FactOriginKind.OPERATION,
    operation: StaticOperationId | None = None,
    role: str = "result",
    context: AnalysisContextId | None = None,
) -> Fact:
    context = context or _context()
    operation = operation or _operation()
    provenance = FactProvenance(
        context_id=context,
        origin_kind=origin,
        operation_id=operation,
    )
    return Fact(
        fact_id=FactId(
            owner=owner,
            kind=FactKind.EQUATION,
            provenance=provenance,
            semantic_key=(role,),
        ),
        formula=formula,
    )


def _tracked(solver: Z3Solver, name: str) -> TrackedSMTVariable:
    return TrackedSMTVariable.create(
        solver,
        name,
        Sort(SortKind.BITVEC, [8]),
        bit_width=8,
    )


def test_immutable_fact_registration_is_idempotent() -> None:
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    fact = _fact(variable.term == 1)

    assert solver.register_immutable_fact(fact)
    assert not solver.register_immutable_fact(fact)
    assert len(solver.get_registered_facts()) == 1
    assert solver.get_assertions() == []


def test_state_fact_registration_is_idempotent() -> None:
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    fact = _fact(
        variable.term != 0,
        owner=FactOwnerKind.STATE_LOCAL,
        role="nonzero",
    )
    state = State(context_id=_context())

    assert state.add_state_fact(fact)
    assert not state.add_state_fact(fact)
    assert state.get_fact_ids() == frozenset({fact.fact_id})
    assert state.get_path_constraints() == [fact.formula]


def test_formula_structure_does_not_define_fact_identity() -> None:
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    formula = variable.term == 1

    immutable = _fact(formula, role="definition")
    state_owned = _fact(
        formula,
        owner=FactOwnerKind.STATE_LOCAL,
        role="assumption",
    )
    other_origin = _fact(
        formula,
        operation=_operation(node_id=2),
        role="definition",
    )

    assert immutable.fact_id != state_owned.fact_id
    assert immutable.fact_id != other_origin.fact_id
    assert state_owned.fact_id != other_origin.fact_id


def test_semantic_state_identity_covers_every_state_component() -> None:
    solver = Z3Solver()
    context = _context()
    base_variable = _tracked(solver, "x_1")
    base = State({"x": base_variable}, context_id=context)
    base_id = base.semantic_id()

    different_value = State({"x": _tracked(solver, "x_2")}, context_id=context)
    assert different_value.semantic_id() != base_id

    fact_state = base.deep_copy()
    fact = _fact(
        base_variable.term != 0,
        owner=FactOwnerKind.STATE_LOCAL,
        role="nonzero",
    )
    fact_state.add_state_fact(fact)
    assert fact_state.semantic_id() != base_id

    storage_state = base.deep_copy()
    storage_state.add_storage_write("0", "x_1")
    assert storage_state.semantic_id() != base_id

    other_context = State(
        {"x": _tracked(solver, "x_1")},
        context_id=_context("C.g()"),
    )
    assert other_context.semantic_id() != base_id

    reachable = IntervalDomain.with_state(base)
    assert reachable.semantic_id() != IntervalDomain.bottom().semantic_id()
    assert reachable.semantic_id() != IntervalDomain.top().semantic_id()
    assert (
        IntervalDomain.bottom(context).semantic_id()
        != IntervalDomain.bottom(_context("C.g()")).semantic_id()
    )


def test_state_copy_preserves_fact_identity_without_aliasing_containers() -> None:
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    fact = _fact(
        variable.term != 0,
        owner=FactOwnerKind.STATE_LOCAL,
        role="nonzero",
    )
    predecessor = State({"x": variable}, context_id=_context())
    predecessor.add_state_fact(fact)
    copied = predecessor.deep_copy()

    assert copied.get_facts()[0] is predecessor.get_facts()[0]
    assert copied.get_fact_ids() == predecessor.get_fact_ids()

    copied.set_variable("y", _tracked(solver, "y_1"))
    copied.add_storage_write("0", "y_1")
    copied_only_fact = _fact(
        variable.term != 1,
        owner=FactOwnerKind.STATE_LOCAL,
        role="copied_only",
    )
    copied.add_state_fact(copied_only_fact)

    assert predecessor.get_variable("y") is None
    assert predecessor.get_storage_writes("0") == []
    assert copied_only_fact.fact_id not in predecessor.get_fact_ids()


def test_telemetry_groups_fact_ownership_and_duplicate_attempts() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    fact = _fact(variable.term == 1)

    try:
        solver.register_immutable_fact(fact)
        solver.register_immutable_fact(fact)
        metrics = telemetry.evaluation.facts

        assert metrics.registrations == 2
        assert metrics.duplicate_registration_attempts == 1
        assert metrics.by_owner == {"immutable_equation": 2}
        assert metrics.by_origin == {"operation": 2}
        assert metrics.by_context == {_context().telemetry_key(): 2}
    finally:
        disable_telemetry()
        reset_telemetry()


def test_unclassified_compatibility_addition_is_detectable() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")

    try:
        solver.assert_constraint(variable.term == 1)

        assert solver.unclassified_additions == 1
        assert telemetry.evaluation.facts.unclassified_additions == 1
        assert telemetry.evaluation.facts.by_owner == {"unclassified_compatibility": 1}
    finally:
        disable_telemetry()
        reset_telemetry()


def test_nonpersistent_ownership_boundaries_do_not_fall_back_to_assertions() -> None:
    solver = Z3Solver()
    variable = _tracked(solver, "x_1")
    query_fact = make_query_fact(variable.term != 0, "feasibility", 0, _context())
    property_fact = _fact(
        variable.term == 1,
        owner=FactOwnerKind.PROPERTY_OBLIGATION,
        origin=FactOriginKind.PROPERTY,
        role="assertion_property",
    )
    loop_fact = _fact(
        variable.term <= 7,
        owner=FactOwnerKind.LOOP_GENERATION,
        origin=FactOriginKind.LOOP,
        role="widened_upper_bound",
    )

    with pytest.raises(RuntimeError, match="active solver scope"):
        solver.add_query_local_assumption(query_fact)
    assert solver.get_assertions() == []

    solver.push()
    solver.add_query_local_assumption(query_fact)
    assert len(solver.get_assertions()) == 1
    solver.pop()
    assert solver.get_assertions() == []

    assert solver.register_property_obligation(property_fact)
    assert solver.get_assertions() == []

    with pytest.raises(NotImplementedError, match="owned by LoopHeaderFixpoint"):
        solver.register_loop_generation_fact(loop_fact)
    assert solver.get_assertions() == []


@dataclass
class _FunctionStub:
    canonical_name: str


@dataclass
class _NodeStub:
    function: _FunctionStub
    node_id: int
    irs_ssa: list[object]


def test_static_operation_identity_uses_static_ir_position() -> None:
    first = object()
    second = object()
    node = _NodeStub(_FunctionStub("C.f()"), 7, [first, second])

    second_id = StaticOperationId.from_operation(second, node)
    first_id = StaticOperationId.from_operation(first, node)

    assert first_id == StaticOperationId.from_operation(first, node)
    assert first_id.ir_position == 0
    assert second_id.ir_position == 1
    assert first_id != second_id


def test_call_symbol_prefix_depends_on_structured_context_not_traversal() -> None:
    callee = _FunctionStub("C.g()")
    first_context = _context().for_call(callee, _operation(node_id=1))
    second_context = _context().for_call(callee, _operation(node_id=2))

    first_prefix = build_call_symbol_prefix("int", "g", first_context)

    assert first_prefix == build_call_symbol_prefix("int", "g", first_context)
    assert first_prefix != build_call_symbol_prefix("int", "g", second_context)
