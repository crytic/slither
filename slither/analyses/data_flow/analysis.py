"""Core range solving functions for Slither data flow interval analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.smt_solver.facts import (
    AnalysisContextId,
    Fact,
    SemanticStateId,
    make_query_fact,
)
from slither.analyses.data_flow.smt_solver.query import (
    FeasibilityStatus,
    QueryPurpose,
)
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.telemetry import SolverTelemetry, get_telemetry
from slither.analyses.data_flow.smt_solver.types import SMTTerm


if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

# Default per-query timeout for Z3 Optimize (milliseconds).
# Used by both the analysis/widening phase and the annotation phase.
# Below 500ms, Z3 Optimize on 256-bit bitvectors frequently returns
# unknown, which silently degrades results to full type-range bounds.
DEFAULT_OPTIMIZE_TIMEOUT_MS = 3000


@dataclass
class RangeQueryConfig:
    """Configuration for range solving queries."""

    path_constraints: list[SMTTerm] | None = None
    state_id: SemanticStateId | None = None
    state_facts: tuple[Fact[SMTTerm], ...] = ()
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS
    skip_optimization: bool = False
    debug: bool = False
    cache: RangeQueryCache | None = None


@dataclass
class VariableMetadata:
    """Extracted metadata from a tracked SMT variable."""

    is_signed: bool
    bit_width: int
    min_bound: int | None
    max_bound: int | None


@dataclass
class RangeSolveContext:
    """Context for range solving operations."""

    solver: SMTSolver
    smt_var: TrackedSMTVariable
    state_id: SemanticStateId | None
    state_facts: tuple[Fact[SMTTerm], ...]
    query_facts: tuple[Fact[SMTTerm], ...]
    telemetry: SolverTelemetry | None
    cache: RangeQueryCache | None


def _check_overflow_possible(
    solver: SMTSolver,
    smt_var: TrackedSMTVariable,
    *,
    state_id: SemanticStateId | None = None,
    state_facts: tuple[Fact[SMTTerm], ...] = (),
    query_facts: tuple[Fact[SMTTerm], ...] = (),
    timeout_ms: int = 500,
) -> bool:
    """Check if overflow or underflow is possible for a variable.

    Tests whether Not(no_overflow) or Not(no_underflow) is satisfiable
    given the current constraints.

    Returns:
        True if overflow/underflow is possible, False otherwise.
    """
    if smt_var.no_overflow is None and smt_var.no_underflow is None:
        return False

    predicates_to_check: list[SMTTerm] = []
    if smt_var.no_overflow is not None:
        predicates_to_check.append(solver.Not(smt_var.no_overflow))
    if smt_var.no_underflow is not None:
        predicates_to_check.append(solver.Not(smt_var.no_underflow))
    if not predicates_to_check:
        return False

    overflow_possible = solver.Or(*predicates_to_check)
    predicate_fact = make_query_fact(
        overflow_possible,
        "overflow_predicate",
        0,
        state_id.context_id if state_id is not None else None,
    )
    result = solver.check_feasibility(
        state_id=state_id,
        state_facts=state_facts,
        query_facts=(*query_facts, predicate_fact),
        purpose=QueryPurpose.OVERFLOW,
        timeout_ms=timeout_ms,
    )
    return result.status is FeasibilityStatus.SAT


# =============================================================================
# RANGE SOLVING HELPERS
# =============================================================================


def _extract_variable_metadata(smt_var: TrackedSMTVariable) -> VariableMetadata | None:
    """Extract metadata from a tracked SMT variable."""
    metadata = smt_var.base.metadata
    is_signed = bool(metadata.get("is_signed", False))
    bit_width = metadata.get("bit_width")

    # Fall back to sort parameters if bit_width not in metadata
    if not isinstance(bit_width, int) and smt_var.sort.parameters:
        bit_width = smt_var.sort.parameters[0]
    if not isinstance(bit_width, int):
        return None

    min_bound = smt_var.interval.lower if smt_var.is_total else None
    max_bound = smt_var.interval.upper if smt_var.is_total else None

    return VariableMetadata(
        is_signed=is_signed,
        bit_width=bit_width,
        min_bound=min_bound,
        max_bound=max_bound,
    )


def _decode_model_value(raw_value: int, meta: VariableMetadata) -> int:
    """Decode a raw Z3 model value according to variable metadata."""
    width = meta.bit_width
    mask = (1 << width) - 1 if width < 256 else (1 << 256) - 1
    value = raw_value & mask
    if meta.is_signed and width > 0:
        half_range = 1 << (width - 1)
        if value >= half_range:
            value -= 1 << width
    if meta.min_bound is not None:
        value = max(meta.min_bound, value)
    if meta.max_bound is not None:
        value = min(meta.max_bound, value)
    return value


def _get_fallback_range(meta: VariableMetadata) -> tuple[dict, dict]:
    """Return conservative type bounds when optimization fails."""
    unsigned_max = (1 << meta.bit_width) - 1
    signed_min = -(1 << (meta.bit_width - 1))
    signed_max = (1 << (meta.bit_width - 1)) - 1
    fallback_min = signed_min if meta.is_signed else 0
    fallback_max = signed_max if meta.is_signed else unsigned_max
    if meta.min_bound is not None:
        fallback_min = meta.min_bound
    if meta.max_bound is not None:
        fallback_max = meta.max_bound
    return (
        {
            "value": fallback_min,
            "overflow": False,
            "bound_status": "abstract",
            "feasibility": None,
        },
        {
            "value": fallback_max,
            "overflow": False,
            "bound_status": "abstract",
            "feasibility": None,
        },
    )


def _build_cache_key(
    smt_var: TrackedSMTVariable,
    solver: SMTSolver,
    state_id: SemanticStateId | None,
) -> tuple[str, tuple]:
    """Build a typed cache key without formula-derived semantic identity."""
    var_id = str(smt_var.term)
    identity = state_id or SemanticStateId(
        reachability="query",
        context_id=AnalysisContextId(solver.function_encoding.encoding_id),
        abstract_values=(),
        active_fact_ids=frozenset(),
        storage_summary=(),
        comparisons=(),
        dependencies=(),
    )
    return var_id, (repr(solver.function_encoding.encoding_id), repr(identity))


def _cached_value_to_dict(val: Any) -> dict:
    """Convert a cached value to a result dictionary."""
    if isinstance(val, dict):
        return {
            "value": val.get("value"),
            "overflow": val.get("overflow", False),
            "bound_status": val.get("bound_status"),
            "feasibility": val.get("feasibility"),
        }
    return {"value": val, "overflow": False}


def _unpack_cached_result(
    cached_result: tuple,
) -> tuple[dict | None, dict | None]:
    """Unpack a cached result into min/max dictionaries."""
    min_val, max_val = cached_result
    if min_val is None or max_val is None:
        return None, None

    return _cached_value_to_dict(min_val), _cached_value_to_dict(max_val)


def _solve_range_with_solver(
    ctx: RangeSolveContext,
    meta: VariableMetadata,
    config: RangeQueryConfig,
) -> tuple[dict | None, dict | None]:
    """Use solver's range solving to find min/max values."""
    if ctx.telemetry:
        ctx.telemetry.count("optimize_min")
        ctx.telemetry.count("optimize_max")

    try:
        result = ctx.solver.solve_range_result(
            term=ctx.smt_var.term,
            state_id=ctx.state_id,
            state_facts=ctx.state_facts,
            query_facts=ctx.query_facts,
            timeout_ms=config.timeout_ms,
            signed=meta.is_signed,
        )

        if result.feasibility is FeasibilityStatus.UNSAT:
            # Return special marker for unreachable paths
            return {"unreachable": True}, {"unreachable": True}

        if result.lower is None or result.upper is None:
            return None, None

        # Decode values according to signedness
        # Note: solve_range now uses signed optimization, so the raw values
        # are correctly ordered. _decode_model_value still converts to signed.
        decoded_min = _decode_model_value(result.lower, meta)
        decoded_max = _decode_model_value(result.upper, meta)

        # Check if overflow is possible given constraints
        has_overflow = _check_overflow_possible(
            ctx.solver,
            ctx.smt_var,
            state_id=ctx.state_id,
            state_facts=ctx.state_facts,
            query_facts=ctx.query_facts,
            timeout_ms=config.timeout_ms,
        )

        min_result = {
            "value": decoded_min,
            "overflow": has_overflow,
            "bound_status": result.lower_status.value,
            "feasibility": result.feasibility.value,
        }
        max_result = {
            "value": decoded_max,
            "overflow": has_overflow,
            "bound_status": result.upper_status.value,
            "feasibility": result.feasibility.value,
        }

        return min_result, max_result
    except (ValueError, TypeError, RuntimeError):
        return None, None


# =============================================================================
# RANGE SOLVING
# =============================================================================


def solve_variable_range(
    solver: SMTSolver,
    smt_var: TrackedSMTVariable,
    config: RangeQueryConfig | None = None,
) -> tuple[dict | None, dict | None]:
    """Solve for min/max values of a variable using SMT optimization.

    Args:
        solver: The SMT solver to use.
        smt_var: The tracked SMT variable to solve range for.
        config: Optional configuration for the range query. If None, uses defaults.

    Returns:
        Tuple of (min_result, max_result) dictionaries with keys:
        - value: The integer value
        - overflow: Boolean indicating if overflow/underflow is possible
    """
    if config is None:
        config = RangeQueryConfig()

    telemetry = get_telemetry()
    context_id = config.state_id.context_id if config.state_id is not None else None
    query_facts = tuple(
        make_query_fact(constraint, "legacy_range_path", index, context_id)
        for index, constraint in enumerate(config.path_constraints or ())
    )
    cache = None if query_facts else config.cache
    ctx = RangeSolveContext(
        solver,
        smt_var,
        config.state_id,
        config.state_facts,
        query_facts,
        telemetry,
        cache,
    )

    cached = _check_cache(ctx, config.skip_optimization)
    if cached is not None:
        return cached

    if not solver.is_bitvector(smt_var.term):
        return None, None

    meta = _extract_variable_metadata(smt_var)
    if meta is None:
        return None, None

    if config.skip_optimization:
        _count_telemetry(telemetry, "range_solve_skipped")
        return _get_fallback_range(meta)

    return _solve_and_cache(ctx, meta, config)


def _check_cache(
    ctx: RangeSolveContext,
    skip_optimization: bool,
) -> tuple[dict | None, dict | None] | None:
    """Check cache for existing result."""
    if ctx.cache is None or skip_optimization:
        return None

    var_id, constraints_tuple = _build_cache_key(ctx.smt_var, ctx.solver, ctx.state_id)
    cached_result = ctx.cache.get(var_id, constraints_tuple)
    if cached_result is not None:
        _count_telemetry(ctx.telemetry, "cache_hit")
        return _unpack_cached_result(cached_result)

    _count_telemetry(ctx.telemetry, "cache_miss")
    return None


def _solve_and_cache(
    ctx: RangeSolveContext,
    meta: VariableMetadata,
    config: RangeQueryConfig,
) -> tuple[dict | None, dict | None]:
    """Solve range and cache result."""
    min_result, max_result = _solve_range_with_solver(ctx, meta, config)

    # Check for unreachable path marker
    if min_result is not None and min_result.get("unreachable"):
        _count_telemetry(ctx.telemetry, "range_solve_unreachable")
        return min_result, max_result

    if min_result is None or max_result is None:
        _count_telemetry(ctx.telemetry, "range_solve_fallback")
        return _get_fallback_range(meta)

    bound_statuses = {
        min_result.get("bound_status"),
        max_result.get("bound_status"),
    }
    if bound_statuses != {"proven"}:
        _count_telemetry(ctx.telemetry, "range_solve_fallback")
        return min_result, max_result

    _count_telemetry(ctx.telemetry, "range_solve_success")

    if ctx.cache is not None:
        var_id, constraints_tuple = _build_cache_key(ctx.smt_var, ctx.solver, ctx.state_id)
        ctx.cache.put(var_id, constraints_tuple, min_result, max_result)

    return min_result, max_result


def _count_telemetry(telemetry: SolverTelemetry | None, name: str) -> None:
    """Count telemetry if enabled."""
    if telemetry:
        telemetry.count(name)
