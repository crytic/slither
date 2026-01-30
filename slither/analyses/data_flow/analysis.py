"""Core range solving functions for Slither data flow interval analysis."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry, SolverTelemetry
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.types import SMTTerm

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

# Default timeout for Optimize queries (milliseconds)
# 500ms is needed for correct results on 256-bit inequality constraints.
DEFAULT_OPTIMIZE_TIMEOUT_MS = 500


@dataclass
class RangeQueryConfig:
    """Configuration for range solving queries."""

    path_constraints: Optional[List[SMTTerm]] = None
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS
    skip_optimization: bool = False
    debug: bool = False
    cache: Optional["RangeQueryCache"] = None


@dataclass
class VariableMetadata:
    """Extracted metadata from a tracked SMT variable."""

    is_signed: bool
    bit_width: int
    min_bound: Optional[int]
    max_bound: Optional[int]


@dataclass
class RangeSolveContext:
    """Context for range solving operations."""

    solver: SMTSolver
    smt_var: TrackedSMTVariable
    path_constraints: Optional[List[SMTTerm]]
    telemetry: Optional[SolverTelemetry]
    cache: Optional["RangeQueryCache"]


# =============================================================================
# RANGE SOLVING HELPERS
# =============================================================================


def _extract_variable_metadata(smt_var: TrackedSMTVariable) -> Optional[VariableMetadata]:
    """Extract metadata from a tracked SMT variable."""
    metadata = smt_var.base.metadata
    is_signed = bool(metadata.get("is_signed", False))
    bit_width = metadata.get("bit_width")

    # Fall back to sort parameters if bit_width not in metadata
    if bit_width is None and smt_var.sort.parameters:
        bit_width = smt_var.sort.parameters[0]
    if bit_width is None:
        return None

    # Extract bounds (these may be ints or None)
    min_bound = metadata.get("min_value")
    max_bound = metadata.get("max_value")

    return VariableMetadata(
        is_signed=is_signed,
        bit_width=int(bit_width),
        min_bound=int(min_bound) if min_bound is not None else None,
        max_bound=int(max_bound) if max_bound is not None else None,
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


def _get_fallback_range(meta: VariableMetadata) -> tuple[Dict, Dict]:
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
        {"value": fallback_min, "overflow": False, "overflow_amount": 0},
        {"value": fallback_max, "overflow": False, "overflow_amount": 0},
    )


def _build_cache_key(
    smt_var: TrackedSMTVariable,
    solver: "SMTSolver",
    path_constraints: Optional[List],
) -> tuple[str, tuple]:
    """Build cache key from variable and constraints."""
    var_id = str(smt_var.term)
    constraint_strs: List[str] = []
    if path_constraints:
        constraint_strs.extend(str(c) for c in path_constraints)
    constraint_strs.extend(str(a) for a in solver.get_assertions())
    return var_id, tuple(constraint_strs)


def _unpack_cached_result(
    cached_result: tuple,
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Unpack a cached result into min/max dictionaries."""
    min_val, max_val = cached_result
    if min_val is None or max_val is None:
        return None, None

    def _to_dict(val: Any) -> Dict:
        if isinstance(val, dict):
            return {
                "value": val.get("value"),
                "overflow": val.get("overflow", False),
                "overflow_amount": val.get("overflow_amount", 0),
            }
        return {"value": val, "overflow": False, "overflow_amount": 0}

    return _to_dict(min_val), _to_dict(max_val)


def _solve_range_with_solver(
    ctx: RangeSolveContext,
    meta: VariableMetadata,
    config: RangeQueryConfig,
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Use solver's range solving to find min/max values."""
    if ctx.telemetry:
        ctx.telemetry.count("optimize_min")
        ctx.telemetry.count("optimize_max")

    try:
        min_val, max_val = ctx.solver.solve_range(
            term=ctx.smt_var.term,
            extra_constraints=ctx.path_constraints,
            timeout_ms=config.timeout_ms,
        )

        if min_val is None or max_val is None:
            return None, None

        # Decode values according to signedness
        decoded_min = _decode_model_value(min_val, meta)
        decoded_max = _decode_model_value(max_val, meta)

        min_result = {"value": decoded_min, "overflow": False, "overflow_amount": 0}
        max_result = {"value": decoded_max, "overflow": False, "overflow_amount": 0}

        return min_result, max_result
    except Exception:
        return None, None


# =============================================================================
# RANGE SOLVING
# =============================================================================


def solve_variable_range(
    solver: SMTSolver,
    smt_var: TrackedSMTVariable,
    config: Optional[RangeQueryConfig] = None,
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Solve for min/max values of a variable using SMT optimization.

    Args:
        solver: The SMT solver to use.
        smt_var: The tracked SMT variable to solve range for.
        config: Optional configuration for the range query. If None, uses defaults.

    Returns:
        Tuple of (min_result, max_result) dictionaries with keys:
        - value: The integer value
        - overflow: Boolean indicating overflow
        - overflow_amount: Amount of overflow if any
    """
    if config is None:
        config = RangeQueryConfig()

    telemetry = get_telemetry()
    ctx = RangeSolveContext(
        solver, smt_var, config.path_constraints, telemetry, config.cache
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
) -> Optional[tuple[Optional[Dict], Optional[Dict]]]:
    """Check cache for existing result."""
    if ctx.cache is None or skip_optimization:
        return None

    var_id, constraints_tuple = _build_cache_key(ctx.smt_var, ctx.solver, ctx.path_constraints)
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
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Solve range and cache result."""
    min_result, max_result = _solve_range_with_solver(ctx, meta, config)

    if min_result is None or max_result is None:
        _count_telemetry(ctx.telemetry, "range_solve_fallback")
        return _get_fallback_range(meta)

    _count_telemetry(ctx.telemetry, "range_solve_success")

    if ctx.cache is not None:
        var_id, constraints_tuple = _build_cache_key(
            ctx.smt_var, ctx.solver, ctx.path_constraints
        )
        ctx.cache.put(var_id, constraints_tuple, min_result, max_result)

    return min_result, max_result


def _count_telemetry(telemetry: Optional[SolverTelemetry], name: str) -> None:
    """Count telemetry if enabled."""
    if telemetry:
        telemetry.count(name)
