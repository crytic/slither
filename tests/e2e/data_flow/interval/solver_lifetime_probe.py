#!/usr/bin/env python3
"""Measure solver and abstract-state lifetimes without changing analysis semantics.

Run with telemetry explicitly enabled by invoking this script::

    SOLC_VERSION=0.8.20 .venv/bin/python \
        tests/e2e/data_flow/interval/solver_lifetime_probe.py \
        tests/e2e/data_flow/interval/contracts/Test_Mul.sol \
        --function test_mul_two_vars --query-variable '^TMP_1$'
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

from slither import Slither
from slither.analyses.data_flow.analyses.interval.analysis.analysis import (
    IntervalAnalysis,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.smt_solver import Z3Solver
from slither.analyses.data_flow.smt_solver.query import RangeInterval
from slither.analyses.data_flow.smt_solver.telemetry import (
    enable_telemetry,
    reset_telemetry,
)
from slither.core.declarations.function import Function


def parse_args() -> argparse.Namespace:
    """Parse probe arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--function", required=True)
    parser.add_argument("--query-variable", help="Regular expression for queried SSA names")
    parser.add_argument(
        "--query-state",
        choices=("current", "none"),
        default="current",
        help="Use current state-local constraints or omit them for a diagnostic control",
    )
    parser.add_argument("--timeout-ms", type=int, default=3000)
    parser.add_argument(
        "--force-refinement",
        action="store_true",
        help="Refine tracked abstract intervals instead of returning them directly",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print lifecycle totals and selected query results without per-node state dumps",
    )
    return parser.parse_args()


def find_function(slither: Slither, name: str) -> Function:
    """Return the single implemented function matching a name."""
    matches = [
        function
        for contract in slither.contracts
        for function in contract.functions_and_modifiers_declared
        if function.is_implemented and function.name == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one implemented function named {name!r}, found {len(matches)}")
    return matches[0]


def query_matching_variables(
    engine: Engine,
    solver: Z3Solver,
    pattern: re.Pattern[str],
    args: argparse.Namespace,
) -> list[dict]:
    """Query each matching variable/state-constraint pair exactly once."""
    queries = []
    seen: set[tuple[str, object]] = set()
    for node, analysis_state in engine.result().items():
        domain = analysis_state.post
        if not isinstance(domain, IntervalDomain):
            continue
        if domain.variant is not DomainVariant.STATE or domain.state is None:
            continue
        state = domain.state
        state_facts = state.get_facts()
        state_id = state.semantic_id()
        if args.query_state == "none":
            empty_state = State(context_id=state.context_id)
            state_facts = ()
            state_id = empty_state.semantic_id()
        for name, variable in state.get_range_variables().items():
            key = (name, state_id)
            if not pattern.search(name) or key in seen:
                continue
            seen.add(key)
            started = time.perf_counter()
            tracked_interval = RangeInterval(variable.interval.lower, variable.interval.upper)
            abstract_sufficient = variable.is_total and (
                variable.interval != variable.type_interval
                or variable.overflow_operation_id is not None
            )
            result = solver.solve_range_result(
                variable.term,
                state_id=state_id,
                state_facts=state_facts,
                timeout_ms=args.timeout_ms,
                signed=bool(variable.base.metadata.get("is_signed", False)),
                fallback_range=tracked_interval,
                abstract_range=(
                    tracked_interval
                    if abstract_sufficient and not args.force_refinement
                    else None
                ),
            )
            queries.append(
                {
                    "node_id": node.node_id,
                    "variable": name,
                    "state_local_constraints": len(state_facts),
                    "feasibility": result.feasibility.value,
                    "lower_status": result.lower_status.value,
                    "upper_status": result.upper_status.value,
                    "lower": result.lower,
                    "upper": result.upper,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                    "total_budget_ms": result.diagnostics.total_budget_ms,
                    "budget_elapsed_ms": round(result.diagnostics.wall_elapsed_ms, 3),
                    "budget_exhausted": result.diagnostics.budget_exhausted,
                    "sessions": len(result.diagnostics.sessions),
                    "backend_elapsed_ms": round(result.diagnostics.elapsed_ms, 3),
                    "fallback_range": (
                        result.fallback_range.to_dict()
                        if result.fallback_range is not None
                        else None
                    ),
                }
            )
    return queries


def node_state_measurements(engine: Engine) -> list[dict]:
    """Serialize live state sizes and revisit counts for every CFG node."""
    measurements = []
    for node, analysis_state in engine.result().items():
        domain = analysis_state.post
        if not isinstance(domain, IntervalDomain):
            continue
        state = domain.state if domain.variant is DomainVariant.STATE else None
        constraints = state.get_path_constraints() if state is not None else []
        unique_constraints = {constraint.sexpr() for constraint in constraints}
        measurements.append(
            {
                "node_id": node.node_id,
                "node_type": str(node.type),
                "predecessors": len(node.fathers),
                "successors": len(node.sons),
                "visits": engine.node_visit_count[node.node_id],
                "variables": len(state.variable_names()) if state is not None else 0,
                "state_local_constraints": len(constraints),
                "state_local_unique_constraints": len(unique_constraints),
                "state_local_duplicate_constraints": len(constraints) - len(unique_constraints),
                "state_local_constraint_formulas": [
                    constraint.sexpr() for constraint in constraints
                ],
            }
        )
    return measurements


def summarize_query_samples(samples: list[dict]) -> dict:
    """Summarize latency and copied-assertion costs across query samples."""
    elapsed = sorted(sample["elapsed_ms"] for sample in samples)
    if not elapsed:
        return {"count": 0, "total_elapsed_ms": 0.0, "copied_assertions": 0}
    by_kind: dict[str, dict] = {}
    for sample in samples:
        summary = by_kind.setdefault(sample["kind"], {"count": 0, "total_elapsed_ms": 0.0})
        summary["count"] += 1
        summary["total_elapsed_ms"] += sample["elapsed_ms"]
    return {
        "count": len(samples),
        "total_elapsed_ms": round(sum(elapsed), 3),
        "median_elapsed_ms": round(elapsed[len(elapsed) // 2], 3),
        "max_elapsed_ms": round(elapsed[-1], 3),
        "copied_assertions": sum(sample["copied_assertions"] for sample in samples),
        "by_kind": by_kind,
    }


def run_probe(args: argparse.Namespace) -> dict:
    """Run one function analysis and return its lifetime measurements."""
    slither = Slither(str(args.contract), compile_force_framework="solc")
    function = find_function(slither, args.function)
    telemetry = enable_telemetry()
    reset_telemetry()
    solver = Z3Solver(use_optimizer=True)
    analysis = IntervalAnalysis(solver=solver, timeout_ms=args.timeout_ms)
    engine = Engine.new(analysis, function)

    started = time.perf_counter()
    engine.run_analysis()
    analysis_elapsed_ms = (time.perf_counter() - started) * 1000
    analysis_query_sessions = telemetry.get_evaluation_metrics().to_dict()["query_sessions"].copy()
    queries = []
    if args.query_variable:
        pattern = re.compile(args.query_variable)
        queries = query_matching_variables(engine, solver, pattern, args)

    assertions = [assertion.sexpr() for assertion in solver.get_assertions()]
    frequencies = Counter(assertions)
    evaluation = telemetry.get_evaluation_metrics().to_dict()
    lifetime = evaluation["solver_lifetime"]
    query_summary = summarize_query_samples(lifetime["query_samples"])
    return {
        "contract": str(args.contract),
        "function": function.name,
        "cfg_nodes": len(function.nodes),
        "analysis_elapsed_ms": round(analysis_elapsed_ms, 3),
        "iterations": engine.iteration_count,
        "final_live_assertions": len(assertions),
        "final_unique_assertions": len(frequencies),
        "final_duplicate_assertions": sum(count - 1 for count in frequencies.values()),
        "duplicate_assertion_formulas": [
            {"formula": formula, "count": count}
            for formula, count in frequencies.items()
            if count > 1
        ],
        "symbolic_variables": len(solver.variables),
        "nodes": node_state_measurements(engine),
        "queries": queries,
        "lifetime": lifetime,
        "fact_ownership": evaluation["facts"],
        "query_sessions": evaluation["query_sessions"],
        "range_refinements": evaluation["range_refinements"],
        "analysis_query_sessions": analysis_query_sessions,
        "state_joins": evaluation["state_joins"],
        "loop_fixpoints": evaluation["loop_fixpoints"],
        "active_query_sessions": solver.active_query_sessions,
        "query_summary": query_summary,
    }


def summarize_probe(result: dict) -> dict:
    """Return the concise evidence used by direct lifecycle checks."""
    lifetime = result["lifetime"]
    facts = result["fact_ownership"]
    return {
        "contract": result["contract"],
        "function": result["function"],
        "cfg_nodes": result["cfg_nodes"],
        "iterations": result["iterations"],
        "analysis_elapsed_ms": result["analysis_elapsed_ms"],
        "visited_nodes": len(lifetime["node_visits"]),
        "final_live_assertions": result["final_live_assertions"],
        "final_duplicate_assertions": result["final_duplicate_assertions"],
        "internal_unclassified_additions": facts["unclassified_additions"],
        "analysis_query_sessions": _summarize_sessions(result["analysis_query_sessions"]),
        "query_sessions": _summarize_sessions(result["query_sessions"]),
        "range_refinements": result["range_refinements"],
        "loop_fixpoints": result["loop_fixpoints"],
        "queries": result["queries"],
        "active_query_sessions": result["active_query_sessions"],
    }


def _summarize_sessions(metrics: dict) -> dict:
    """Drop high-cardinality identities from session lifecycle output."""
    keys = (
        "created",
        "closed",
        "active",
        "cleanup_imbalances",
        "timeout_results",
        "compatibility_query_facts",
        "by_purpose",
        "feasibility_statuses",
        "bound_statuses",
    )
    return {key: metrics[key] for key in keys}


def main() -> None:
    """Run the command-line probe."""
    args = parse_args()
    result = run_probe(args)
    if args.summary_only:
        result = summarize_probe(result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
