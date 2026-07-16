"""Tests for opt-in solver-lifetime telemetry."""

from slither.analyses.data_flow.smt_solver import Z3Solver
from slither.analyses.data_flow.smt_solver.telemetry import (
    disable_telemetry,
    enable_telemetry,
    get_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.smt_solver.types import RangeSolveStatus, Sort, SortKind


def test_lifetime_telemetry_is_disabled_by_default() -> None:
    disable_telemetry()
    reset_telemetry()
    solver = Z3Solver(use_optimizer=True)
    variable = solver.get_or_declare_const("disabled", Sort(SortKind.BITVEC, [8]))

    solver.assert_constraint(variable.term == 1)
    status, lower, upper = solver.solve_range(variable.term, timeout_ms=1000)

    telemetry = get_telemetry()
    assert telemetry is not None
    assert status is RangeSolveStatus.SUCCESS
    assert (lower, upper) == (1, 1)
    assert telemetry.evaluation.solver_lifetime.assertion_additions == 0
    assert telemetry.evaluation.solver_lifetime.query_samples == []


def test_lifetime_telemetry_measures_duplicates_scopes_and_queries() -> None:
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = Z3Solver(use_optimizer=True)
    variable = solver.get_or_declare_const("enabled", Sort(SortKind.BITVEC, [8]))
    constraint = variable.term == 1

    try:
        solver.assert_constraint(constraint)
        solver.assert_constraint(constraint)
        solver.push()
        solver.assert_constraint(variable.term != 2)
        solver.pop()
        status, lower, upper = solver.solve_range(variable.term, timeout_ms=1000)

        lifetime = telemetry.evaluation.solver_lifetime
        assert status is RangeSolveStatus.SUCCESS
        assert (lower, upper) == (1, 1)
        assert lifetime.assertion_additions == 3
        assert lifetime.unique_assertions == 2
        assert lifetime.duplicate_assertions == 1
        assert lifetime.live_assertions == 2
        assert lifetime.max_live_assertions == 3
        assert lifetime.symbolic_variables == 1
        sessions = telemetry.evaluation.query_sessions
        assert sessions.created == sessions.closed == 3
        assert sessions.active == 0
        assert sessions.assertion_copies == 6
        assert sessions.compatibility_query_facts == 6
        assert len(solver.get_assertions()) == 2
    finally:
        disable_telemetry()
        reset_telemetry()
