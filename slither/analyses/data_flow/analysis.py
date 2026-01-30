"""Core analysis functions for Slither data flow interval analysis."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import sys

from slither import Slither
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry, SolverTelemetry
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.analyses.data_flow.models import (
    VariableResult,
    FunctionResult,
    ContractResult,
)
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function

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


@dataclass
class CollectionConfig:
    """Config for variable result collection."""

    solver: SMTSolver
    timeout_ms: int
    skip_range_solving: bool
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

        # For now, overflow detection is not supported in solver-agnostic mode
        # TODO: Add overflow tracking to solve_range interface
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


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================


def analyze_function_quiet(
    function: Function,
    analysis: IntervalAnalysis,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_range_solving: bool = False,
    cache: Optional["RangeQueryCache"] = None,
) -> FunctionResult:
    """Run interval analysis on a function and return structured results."""
    result = FunctionResult(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
    )

    if not function.nodes:
        result.error = "Function has no nodes"
        return result

    try:
        results = _run_analysis(function, analysis)
        solver = analysis.solver
        if not solver:
            result.error = "No solver available"
            return result

        nodes_to_process = _get_nodes_to_process(function, results)
        return_value_vars = _find_return_value_vars(function)
        coll_config = CollectionConfig(solver, timeout_ms, skip_range_solving, cache)

        _collect_variable_results(
            nodes_to_process, results, result, return_value_vars, coll_config
        )

    except Exception as e:
        _handle_analysis_exception(e, function)
        raise

    return result


def _run_analysis(
    function: Function, analysis: IntervalAnalysis
) -> Dict[Node, AnalysisState[IntervalAnalysis]]:
    """Run the engine analysis."""
    engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)
    engine.run_analysis()
    return engine.result()


def _get_nodes_to_process(
    function: Function, results: Dict[Node, AnalysisState[IntervalAnalysis]]
) -> List[Node]:
    """Get nodes to process for result collection."""
    return_nodes = [node for node in function.nodes if not node.sons]
    if not return_nodes:
        return_nodes = [function.nodes[-1]] if function.nodes else []

    all_unreachable = all(
        node not in results or results[node].post.variant != DomainVariant.STATE
        for node in return_nodes
    )

    if all_unreachable:
        for node in reversed(function.nodes):
            if node in results and results[node].post.variant == DomainVariant.STATE:
                return [node]

    return return_nodes


def _find_return_value_vars(function: Function) -> set[str]:
    """Find variable names that are returned from the function."""
    return_vars: set[str] = set()
    for node in function.nodes:
        for ir in node.irs:
            if type(ir).__name__ == "Return" and hasattr(ir, "values"):
                for val in ir.values:
                    val_name = getattr(val, "name", None)
                    if val_name:
                        return_vars.add(val_name)
    return return_vars


def _collect_variable_results(
    nodes: List[Node],
    results: Dict[Node, AnalysisState[IntervalAnalysis]],
    result: FunctionResult,
    return_value_vars: set[str],
    config: CollectionConfig,
) -> None:
    """Collect variable results from nodes."""
    for node in nodes:
        if node not in results:
            continue
        state = results[node]
        if state.post.variant != DomainVariant.STATE:
            continue

        post_state_vars = state.post.state.get_range_variables()
        used_vars = state.post.state.get_used_variables()
        path_constraints = state.post.state.get_path_constraints()

        for var_name, smt_var in post_state_vars.items():
            if _should_skip_var(var_name, used_vars, return_value_vars, result):
                continue

            var_result = _solve_and_create_result(var_name, smt_var, path_constraints, config)
            if var_result:
                result.variables[var_name] = var_result


def _should_skip_var(
    var_name: str, used_vars: set, return_value_vars: set[str], result: FunctionResult
) -> bool:
    """Check if variable should be skipped."""
    if var_name.startswith("CONST_"):
        return True
    if var_name.startswith("TMP_") and var_name not in return_value_vars:
        return True
    if var_name.startswith("REF_"):
        return True
    if var_name not in used_vars:
        return True
    if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
        return True
    if var_name in result.variables:
        return True
    return False


def _solve_and_create_result(
    var_name: str,
    smt_var: TrackedSMTVariable,
    path_constraints,
    config: CollectionConfig,
) -> Optional[VariableResult]:
    """Solve variable range and create result."""
    range_config = RangeQueryConfig(
        path_constraints=path_constraints,
        timeout_ms=config.timeout_ms,
        skip_optimization=config.skip_range_solving,
        cache=config.cache,
    )
    min_result, max_result = solve_variable_range(config.solver, smt_var, range_config)

    if not (min_result and max_result):
        return None

    has_overflow = min_result.get("overflow", False) or max_result.get("overflow", False)
    is_wrapped = min_result["value"] > max_result["value"]

    if is_wrapped:
        range_str = f"[{max_result['value']}, {min_result['value']}]"
    else:
        range_str = f"[{min_result['value']}, {max_result['value']}]"

    return VariableResult(
        name=var_name,
        range_str=range_str,
        overflow="YES" if has_overflow else "NO",
        overflow_amount=max(
            min_result.get("overflow_amount", 0),
            max_result.get("overflow_amount", 0),
        ),
    )


def _handle_analysis_exception(e: Exception, function: Function) -> None:
    """Handle exception during analysis."""
    from slither.analyses.data_flow.logger import get_logger, LogMessages

    logger = get_logger()
    logger.exception(
        LogMessages.ERROR_ANALYSIS_FAILED,
        error=str(e),
        function_name=function.name,
        embed_on_error=False,
    )


def analyze_contract_quiet(
    contract_path: Path,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_range_solving: bool = False,
) -> List[ContractResult]:
    """Analyze a contract file and return structured results.

    Args:
        contract_path: Path to the contract file.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_range_solving: If True, skip SMT optimization and use type bounds.
    """
    from slither.analyses.data_flow.smt_solver import Z3Solver
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

    results: List[ContractResult] = []

    try:
        slither = Slither(str(contract_path))
        contracts: List[Contract] = []
        if slither.compilation_units:
            for cu in slither.compilation_units:
                contracts.extend(cu.contracts)
        else:
            contracts = slither.contracts

        for contract in contracts:
            contract_result = ContractResult(
                contract_file=contract_path.name,
                contract_name=contract.name,
            )

            functions = contract.functions_and_modifiers_declared
            implemented_functions = [
                f for f in functions if f.is_implemented and not f.is_constructor
            ]

            # Create shared cache for all functions in this contract
            cache = RangeQueryCache(max_size=1000)

            for function in implemented_functions:
                solver = Z3Solver(use_optimizer=True)
                analysis = IntervalAnalysis(solver=solver)

                func_result = analyze_function_quiet(
                    function,
                    analysis,
                    timeout_ms=timeout_ms,
                    skip_range_solving=skip_range_solving,
                    cache=cache,
                )
                contract_result.functions[function.name] = func_result

            results.append(contract_result)

    except Exception:
        # Log error with context, then stop execution
        from slither.analyses.data_flow.logger import get_logger

        logger = get_logger()
        logger.exception(
            "Failed to analyze contract: {contract_path}",
            contract_path=str(contract_path),
            embed_on_error=False,
        )
        raise

    return results


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    from slither.analyses.data_flow.cli import main

    sys.exit(main())
