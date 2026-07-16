"""Stage 5 abstract-first range refinement and total-budget tests."""

from __future__ import annotations

from typing import Any

from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analysis import RangeQueryConfig, solve_variable_range
from slither.analyses.data_flow.smt_solver import Z3Solver
from slither.analyses.data_flow.smt_solver.facts import (
    AnalysisContextId,
    EncodingId,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.query import (
    BoundOutcome,
    BoundStatus,
    FeasibilityResult,
    FeasibilityStatus,
    QueryBudget,
    QueryDiagnostics,
    RangeInterval,
    empty_state_id,
)
from slither.analyses.data_flow.smt_solver.telemetry import (
    disable_telemetry,
    enable_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind


ENCODING_ID = EncodingId("range_refinement.sol", "C.f()")
CONTEXT_ID = AnalysisContextId(ENCODING_ID)


def _solver() -> Z3Solver:
    solver = Z3Solver()
    solver.bind_function_encoding(ENCODING_ID)
    return solver


def _tracked(
    solver: Z3Solver,
    interval: NumericInterval,
    *,
    operation_result: bool,
) -> TrackedSMTVariable:
    variable = TrackedSMTVariable.create(
        solver,
        "x",
        Sort(SortKind.BITVEC, [8]),
        bit_width=8,
    ).with_interval(interval)
    if operation_result:
        variable = variable.with_overflow_predicates(
            operation_id=StaticOperationId(ENCODING_ID, 1, 0)
        )
    return variable


def test_abstract_top_operation_avoids_every_solver_session() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = _solver()
    variable = _tracked(solver, NumericInterval(0, 255), operation_result=True)
    state = State({"x": variable}, context_id=CONTEXT_ID)
    before_encoding = solver.function_encoding.fact_ids()
    before_state = state.semantic_id()

    try:
        lower, upper = solve_variable_range(
            solver,
            variable,
            RangeQueryConfig(
                state_id=before_state,
                state_facts=state.get_facts(),
                timeout_ms=1000,
            ),
        )

        assert lower == {
            "value": 0,
            "overflow": False,
            "bound_status": "abstract",
            "feasibility": "not_attempted",
        }
        assert upper == {
            "value": 255,
            "overflow": False,
            "bound_status": "abstract",
            "feasibility": "not_attempted",
        }
        sessions = telemetry.evaluation.query_sessions
        assert sessions.created == sessions.closed == sessions.active == 0
        refinements = telemetry.evaluation.range_refinements
        assert refinements.abstract_only == refinements.sessions_avoided == 1
        assert solver.function_encoding.fact_ids() == before_encoding
        assert state.semantic_id() == before_state
    finally:
        disable_telemetry()


def test_finite_abstract_interval_avoids_refinement_by_default() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = _solver()
    variable = _tracked(solver, NumericInterval(10, 20), operation_result=False)
    state = State({"x": variable}, context_id=CONTEXT_ID)

    try:
        lower, upper = solve_variable_range(
            solver,
            variable,
            RangeQueryConfig(
                state_id=state.semantic_id(),
                state_facts=state.get_facts(),
                timeout_ms=1000,
            ),
        )

        assert lower is not None and upper is not None
        assert (lower["value"], upper["value"]) == (10, 20)
        assert lower["bound_status"] == upper["bound_status"] == "abstract"
        assert telemetry.evaluation.query_sessions.created == 0
    finally:
        disable_telemetry()


def test_optional_refinement_uses_tracked_fallback_and_balances_sessions() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = _solver()
    variable = _tracked(solver, NumericInterval(10, 20), operation_result=False)
    state = State({"x": variable}, context_id=CONTEXT_ID)
    encoding_before = solver.function_encoding.fact_ids()
    state_before = state.semantic_id()

    try:
        lower, upper = solve_variable_range(
            solver,
            variable,
            RangeQueryConfig(
                state_id=state.semantic_id(),
                state_facts=state.get_facts(),
                timeout_ms=1000,
                refine_abstract=True,
            ),
        )

        assert lower is not None and upper is not None
        assert (lower["value"], upper["value"]) == (10, 20)
        assert lower["bound_status"] == upper["bound_status"] == "proven"
        sessions = telemetry.evaluation.query_sessions
        assert sessions.created == sessions.closed == 3
        assert sessions.active == sessions.cleanup_imbalances == 0
        assert sessions.query_facts_materialized == 6
        assert solver.function_encoding.fact_ids() == encoding_before
        assert state.semantic_id() == state_before
    finally:
        disable_telemetry()


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance_ms(self, milliseconds: int) -> None:
        self.now += milliseconds / 1000


class _BudgetSolver(Z3Solver):
    minimum_session_budget_ms = 0
    backend_timeout_fraction = 1.0

    def __init__(self, clock: _FakeClock) -> None:
        super().__init__()
        self.clock = clock
        self.allocations: list[tuple[str, int]] = []

    def _range_feasibility(self, *, timeout_ms: int, **query: Any) -> FeasibilityResult:
        del query
        self.allocations.append(("feasibility", timeout_ms))
        self.clock.advance_ms(2)
        state_id = empty_state_id(self.function_encoding.encoding_id)
        return FeasibilityResult(
            FeasibilityStatus.SAT,
            self.function_encoding.encoding_id,
            state_id,
            QueryDiagnostics(),
        )

    def _execute_bound_query(
        self,
        term: Any,
        objective_term: Any,
        *,
        purpose: Any,
        timeout_ms: int,
        **query: Any,
    ) -> BoundOutcome:
        del term, objective_term, query
        self.allocations.append((purpose.value, timeout_ms))
        self.clock.advance_ms(timeout_ms)
        return BoundOutcome(3, BoundStatus.PROVEN)


def test_one_total_budget_retains_lower_and_skips_expired_upper() -> None:
    clock = _FakeClock()
    solver = _BudgetSolver(clock)
    solver.bind_function_encoding(ENCODING_ID)
    term = solver.get_or_declare_const("x", Sort(SortKind.BITVEC, [8])).term
    budget = QueryBudget(10, clock=clock)

    result = solver.solve_range_result(
        term,
        timeout_ms=1000,
        fallback_range=RangeInterval(0, 255),
        budget=budget,
    )

    assert solver.allocations == [("feasibility", 10), ("lower_bound", 8)]
    assert result.lower == 3
    assert result.lower_status is BoundStatus.PROVEN
    assert result.upper == 255
    assert result.upper_status is BoundStatus.TIMEOUT
    assert result.fallback_range == RangeInterval(0, 255)
    assert result.diagnostics.total_budget_ms == 10
    assert result.diagnostics.budget_exhausted
    assert result.diagnostics.wall_elapsed_ms == 10
    assert solver.active_query_sessions == 0


def test_tiny_budget_is_not_spent_opening_a_z3_session() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = _solver()
    term = solver.get_or_declare_const("tiny", Sort(SortKind.BITVEC, [8])).term

    try:
        result = solver.solve_range_result(term, timeout_ms=20)

        assert result.lower_status is BoundStatus.TIMEOUT
        assert result.upper_status is BoundStatus.TIMEOUT
        assert result.diagnostics.budget_exhausted
        sessions = telemetry.evaluation.query_sessions
        assert sessions.created == sessions.closed == 0
    finally:
        disable_telemetry()
