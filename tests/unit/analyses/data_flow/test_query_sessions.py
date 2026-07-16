"""Tests for Stage 2 query materialization and solver-session isolation."""

from __future__ import annotations

from dataclasses import replace

import pytest
from z3 import Optimize, sat, unknown, unsat

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.require_assert import (
    RequireAssertHandler,
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
from slither.analyses.data_flow.smt_solver.query import (
    BoundStatus,
    FeasibilityStatus,
    QueryPurpose,
    RangeInterval,
)
from slither.analyses.data_flow.smt_solver.telemetry import (
    disable_telemetry,
    enable_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.analyses.data_flow.analysis import _check_overflow_possible


ENCODING_ID = EncodingId("query_sessions.sol", "C.f()")
CONTEXT_ID = AnalysisContextId(ENCODING_ID)


def _solver() -> tuple[Z3Solver, object]:
    solver = Z3Solver()
    solver.bind_function_encoding(ENCODING_ID)
    variable = solver.get_or_declare_const("x", Sort(SortKind.BITVEC, [8]))
    return solver, variable.term


def _fact(
    formula: object,
    *,
    owner: FactOwnerKind,
    role: str,
) -> Fact:
    return Fact(
        fact_id=FactId(
            owner=owner,
            kind=FactKind.PROPERTY if owner is FactOwnerKind.PROPERTY_OBLIGATION else (
                FactKind.PATH_CONDITION
            ),
            provenance=FactProvenance(
                context_id=CONTEXT_ID,
                origin_kind=(
                    FactOriginKind.PROPERTY
                    if owner is FactOwnerKind.PROPERTY_OBLIGATION
                    else FactOriginKind.CFG_EDGE
                ),
            ),
            semantic_key=(role,),
        ),
        formula=formula,
    )


def _state(formula: object, role: str) -> State:
    state = State(context_id=CONTEXT_ID)
    state.add_state_fact(_fact(formula, owner=FactOwnerKind.STATE_LOCAL, role=role))
    return state


class _UnknownBackend:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def add(self, *formulas: object) -> None:
        del formulas

    def check(self) -> object:
        return unknown

    def reason_unknown(self) -> str:
        return self.reason

    def minimize(self, term: object) -> None:
        del term

    def maximize(self, term: object) -> None:
        del term


class _FixedBackend(_UnknownBackend):
    def __init__(self, result: object) -> None:
        super().__init__("unused")
        self.result = result

    def check(self) -> object:
        return self.result


class _ErrorBackend(_UnknownBackend):
    def check(self) -> object:
        raise RuntimeError("simulated backend error")


class _FeasibilityOutcomeSolver(Z3Solver):
    def __init__(self, backend: object) -> None:
        super().__init__()
        self.backend = backend

    def _create_feasibility_backend(self, timeout_ms: int) -> object:
        del timeout_ms
        return self.backend


class _PartialBoundSolver(Z3Solver):
    def __init__(self, failed_backend: object) -> None:
        super().__init__()
        self.failed_backend = failed_backend
        self.optimizer_count = 0

    def _create_optimizer_backend(self, timeout_ms: int) -> object:
        self.optimizer_count += 1
        if self.optimizer_count == 2:
            return self.failed_backend
        optimizer = Optimize()
        optimizer.set("timeout", timeout_ms)
        return optimizer


class _TimeoutRangeSolver(_FeasibilityOutcomeSolver):
    def _create_optimizer_backend(self, timeout_ms: int) -> object:
        del timeout_ms
        return _UnknownBackend("timeout")


def _bind_test_variable(solver: Z3Solver) -> object:
    solver.bind_function_encoding(ENCODING_ID)
    return solver.get_or_declare_const("x", Sort(SortKind.BITVEC, [8])).term


def test_function_encoding_is_immutable_across_success_and_unsat_queries() -> None:
    solver, term = _solver()
    immutable = _fact(term == 7, owner=FactOwnerKind.IMMUTABLE_EQUATION, role="definition")
    solver.register_immutable_fact(immutable)
    before = solver.function_encoding.fact_ids()

    successful = solver.solve_range_result(term, timeout_ms=1000)
    unsat_state = _state(term != 7, "contradiction")
    infeasible = solver.check_feasibility(
        state_id=unsat_state.semantic_id(),
        state_facts=unsat_state.get_facts(),
    )

    assert (successful.lower, successful.upper) == (7, 7)
    assert infeasible.status is FeasibilityStatus.UNSAT
    assert solver.function_encoding.fact_ids() == before
    assert solver.get_assertions() == []
    assert solver.active_query_sessions == 0


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        (_UnknownBackend("timeout"), FeasibilityStatus.TIMEOUT),
        (_UnknownBackend("incomplete theory"), FeasibilityStatus.UNKNOWN),
        (_ErrorBackend("unused"), FeasibilityStatus.ERROR),
    ],
)
def test_feasibility_statuses_cleanup_every_backend_outcome(
    backend: object,
    expected: FeasibilityStatus,
) -> None:
    solver = _FeasibilityOutcomeSolver(backend)
    term = _bind_test_variable(solver)
    state = _state(term < 10, "upper")
    before_id = state.semantic_id()
    before_encoding = solver.function_encoding.fact_ids()

    result = solver.check_feasibility(
        state_id=before_id,
        state_facts=state.get_facts(),
        timeout_ms=1,
    )

    assert result.status is expected
    assert state.semantic_id() == before_id
    assert solver.function_encoding.fact_ids() == before_encoding
    assert solver.active_query_sessions == 0
    assert result.diagnostics.cleanup_balanced


def test_raised_python_exception_closes_session_without_mutation() -> None:
    solver, term = _solver()
    immutable = _fact(
        term == term,
        owner=FactOwnerKind.IMMUTABLE_EQUATION,
        role="identity",
    )
    solver.register_immutable_fact(immutable)
    state = _state(term < 10, "upper")
    before_state = state.semantic_id()
    before_encoding = solver.function_encoding.fact_ids()
    session = solver.create_query_session(
        purpose=QueryPurpose.FEASIBILITY,
        timeout_ms=100,
        state_id=before_state,
        state_facts=state.get_facts(),
    )

    with pytest.raises(ValueError, match="simulated Python exception"):
        with session:
            raise ValueError("simulated Python exception")

    assert solver.active_query_sessions == 0
    assert solver.function_encoding.fact_ids() == before_encoding
    assert state.semantic_id() == before_state
    assert session.diagnostics.cleanup_balanced


@pytest.mark.parametrize("purpose", [QueryPurpose.REQUIRE, QueryPurpose.ASSERT])
@pytest.mark.parametrize(
    ("backend", "is_unsatisfiable"),
    [
        (_FixedBackend(sat), False),
        (_FixedBackend(unsat), True),
        (_UnknownBackend("timeout"), False),
        (_ErrorBackend("unused"), False),
    ],
)
def test_require_assert_feasibility_never_persists_continuation_condition(
    purpose: QueryPurpose,
    backend: object,
    is_unsatisfiable: bool,
) -> None:
    solver = _FeasibilityOutcomeSolver(backend)
    term = _bind_test_variable(solver)
    state = _state(term == 1, "successful_continuation")
    domain = IntervalDomain.with_state(state)
    handler = RequireAssertHandler(solver)
    before_state = state.semantic_id()

    result = handler._is_unsatisfiable(domain, purpose)

    assert result is is_unsatisfiable
    assert state.semantic_id() == before_state
    assert solver.function_encoding.fact_ids() == frozenset()
    assert solver.get_assertions() == []
    assert solver.active_query_sessions == 0


def test_query_sessions_isolate_opposite_assumptions() -> None:
    solver, term = _solver()
    state_id = State(context_id=CONTEXT_ID).semantic_id()
    positive = make_query_fact(term == 1, "positive", 0, CONTEXT_ID)
    negative = make_query_fact(term != 1, "negative", 0, CONTEXT_ID)
    session_a = solver.create_query_session(
        purpose=QueryPurpose.FEASIBILITY,
        timeout_ms=100,
        state_id=state_id,
        query_facts=(positive,),
    )
    session_b = solver.create_query_session(
        purpose=QueryPurpose.FEASIBILITY,
        timeout_ms=100,
        state_id=state_id,
        query_facts=(negative,),
    )

    assert session_a.materialization.query_facts == (positive,)
    assert session_b.materialization.query_facts == (negative,)
    session_a.close(feasibility_status=FeasibilityStatus.SAT)
    assert session_b.materialization.query_facts == (negative,)
    assert solver.active_query_sessions == 1
    session_b.close(feasibility_status=FeasibilityStatus.SAT)
    assert session_a.diagnostics.cleanup_balanced
    assert session_b.diagnostics.cleanup_balanced
    assert solver.active_query_sessions == 0
    assert solver.function_encoding.fact_ids() == frozenset()


def test_same_term_uses_only_the_selected_state_facts() -> None:
    solver, term = _solver()
    sort = Sort(SortKind.BITVEC, [8])
    state_a = _state(solver.bv_ult(term, solver.create_constant(10, sort)), "below_ten")
    state_b = _state(solver.bv_ugt(term, solver.create_constant(20, sort)), "above_twenty")

    result_a = solver.solve_range_result(
        term,
        state_id=state_a.semantic_id(),
        state_facts=state_a.get_facts(),
        timeout_ms=1000,
    )
    result_b = solver.solve_range_result(
        term,
        state_id=state_b.semantic_id(),
        state_facts=state_b.get_facts(),
        timeout_ms=1000,
    )

    assert (result_a.lower, result_a.upper) == (0, 9)
    assert (result_b.lower, result_b.upper) == (21, 255)
    assert result_a.state_id != result_b.state_id


@pytest.mark.parametrize(
    ("failed_backend", "failed_status"),
    [
        (_UnknownBackend("timeout"), BoundStatus.TIMEOUT),
        (_UnknownBackend("incomplete theory"), BoundStatus.UNKNOWN),
        (_ErrorBackend("unused"), BoundStatus.ERROR),
    ],
)
def test_partial_bound_retains_successful_minimum(
    failed_backend: object,
    failed_status: BoundStatus,
) -> None:
    solver = _PartialBoundSolver(failed_backend)
    term = _bind_test_variable(solver)
    immutable = _fact(
        term == term,
        owner=FactOwnerKind.IMMUTABLE_EQUATION,
        role="identity",
    )
    solver.register_immutable_fact(immutable)
    before_encoding = solver.function_encoding.fact_ids()

    result = solver.solve_range_result(term, timeout_ms=1000)

    assert result.lower == 0
    assert result.lower_status is BoundStatus.PROVEN
    assert result.upper == 255
    assert result.upper_status is failed_status
    assert result.fallback_range == RangeInterval(0, 255)
    assert result.diagnostics.cleanup_balanced
    assert solver.active_query_sessions == 0
    assert solver.function_encoding.fact_ids() == before_encoding


def test_proven_timeout_and_abstract_full_ranges_are_tagged_differently() -> None:
    proven_solver, proven_term = _solver()
    proven = proven_solver.solve_range_result(proven_term, timeout_ms=1000)

    timeout_solver = _TimeoutRangeSolver(_UnknownBackend("timeout"))
    timeout_term = _bind_test_variable(timeout_solver)
    timed_out = timeout_solver.solve_range_result(timeout_term, timeout_ms=1)

    abstract_solver, abstract_term = _solver()
    abstract = abstract_solver.solve_range_result(
        abstract_term,
        abstract_range=RangeInterval(0, 255),
        timeout_ms=1000,
    )

    assert (proven.lower_status, proven.upper_status) == (
        BoundStatus.PROVEN,
        BoundStatus.PROVEN,
    )
    assert (timed_out.lower_status, timed_out.upper_status) == (
        BoundStatus.TIMEOUT,
        BoundStatus.TIMEOUT,
    )
    assert (abstract.lower_status, abstract.upper_status) == (
        BoundStatus.ABSTRACT,
        BoundStatus.ABSTRACT,
    )
    assert proven.fallback_range is None
    assert timed_out.fallback_range == abstract.fallback_range == RangeInterval(0, 255)
    assert proven.to_dict()["lower_status"] == "proven"
    assert timed_out.to_dict()["lower_status"] == "timeout"
    assert abstract.to_dict()["lower_status"] == "abstract"


def test_raw_extra_constraints_are_ephemeral_compatibility_facts() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver, term = _solver()
    before = solver.function_encoding.fact_ids()

    try:
        status, lower, upper = solver.solve_range(
            term,
            extra_constraints=[term == 9],
            timeout_ms=1000,
        )

        sessions = telemetry.evaluation.query_sessions
        assert status.value == "success"
        assert (lower, upper) == (9, 9)
        assert sessions.compatibility_query_facts == 3
        assert telemetry.evaluation.facts.unclassified_additions == 0
        assert solver.unclassified_additions == 0
        assert solver.function_encoding.fact_ids() == before
        assert solver.get_assertions() == []
        assert sessions.created == sessions.closed == 3
        assert sessions.active == 0
    finally:
        disable_telemetry()
        reset_telemetry()


def test_overflow_probe_materializes_typed_state_and_query_facts() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver, left = _solver()
    sort = Sort(SortKind.BITVEC, [8])
    right = solver.get_or_declare_const("right", sort).term
    tracked = TrackedSMTVariable.create(solver, "result", sort, bit_width=8)
    tracked = tracked.with_overflow_predicates(
        no_overflow=solver.bv_add_no_overflow(left, right, signed=False),
        operation_id=StaticOperationId(ENCODING_ID, 12, 0),
    )
    definition = _fact(
        tracked.term == solver.bv_add(left, right),
        owner=FactOwnerKind.IMMUTABLE_EQUATION,
        role="addition",
    )
    solver.register_immutable_fact(definition)
    state = State(context_id=CONTEXT_ID)
    state.add_state_fact(_fact(left == 255, owner=FactOwnerKind.STATE_LOCAL, role="left"))
    state.add_state_fact(_fact(right == 1, owner=FactOwnerKind.STATE_LOCAL, role="right"))
    before_state = state.semantic_id()
    before_encoding = solver.function_encoding.fact_ids()

    try:
        possible = _check_overflow_possible(
            solver,
            tracked,
            state_id=before_state,
            state_facts=state.get_facts(),
            timeout_ms=1000,
        )

        sessions = telemetry.evaluation.query_sessions
        assert possible
        assert sessions.by_purpose == {"overflow": 1}
        assert sessions.state_facts_materialized == 2
        assert sessions.query_facts_materialized == 1
        assert sessions.compatibility_query_facts == 0
        assert sessions.created == sessions.closed == 1
        assert state.semantic_id() == before_state
        assert solver.function_encoding.fact_ids() == before_encoding
        assert solver.active_query_sessions == 0
    finally:
        disable_telemetry()
        reset_telemetry()


def test_property_obligations_materialize_only_when_selected() -> None:
    solver, term = _solver()
    first = _fact(term == 1, owner=FactOwnerKind.PROPERTY_OBLIGATION, role="first")
    second = _fact(term == 2, owner=FactOwnerKind.PROPERTY_OBLIGATION, role="second")
    solver.register_property_obligation(first)
    solver.register_property_obligation(second)
    state_id = State(context_id=CONTEXT_ID).semantic_id()

    ordinary = solver.create_query_session(
        purpose=QueryPurpose.FEASIBILITY,
        timeout_ms=100,
        state_id=state_id,
    )
    selected = solver.create_query_session(
        purpose=QueryPurpose.PROPERTY,
        timeout_ms=100,
        state_id=state_id,
        property_fact=first,
    )

    assert ordinary.materialization.property_fact is None
    assert selected.materialization.property_fact is first
    assert second not in selected.materialization.facts
    ordinary.close(feasibility_status=FeasibilityStatus.SAT)
    selected.close(feasibility_status=FeasibilityStatus.SAT)
    assert solver.get_property_obligations() == (first, second)
    assert solver.active_query_sessions == 0


def test_materialization_rejects_state_id_fact_mismatch() -> None:
    solver, term = _solver()
    state = _state(term < 10, "upper")
    wrong_id = replace(state.semantic_id(), active_fact_ids=frozenset())

    with pytest.raises(ValueError, match="do not match SemanticStateId"):
        solver.create_query_session(
            purpose=QueryPurpose.FEASIBILITY,
            timeout_ms=100,
            state_id=wrong_id,
            state_facts=state.get_facts(),
        )

    assert solver.active_query_sessions == 0
