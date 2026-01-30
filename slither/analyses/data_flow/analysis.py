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

    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS
    skip_optimization: bool = False
    debug: bool = False


@dataclass
class VariableMetadata:
    """Extracted metadata from a tracked SMT variable."""

    is_signed: bool
    bit_width: int
    min_bound: Optional[int]
    max_bound: Optional[int]


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
    solver: SMTSolver,
    smt_var: TrackedSMTVariable,
    meta: VariableMetadata,
    path_constraints: Optional[List[SMTTerm]],
    config: RangeQueryConfig,
    telemetry: Optional[SolverTelemetry],
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Use solver's range solving to find min/max values."""
    if telemetry:
        telemetry.count("optimize_min")
        telemetry.count("optimize_max")

    try:
        min_val, max_val = solver.solve_range(
            term=smt_var.term,
            extra_constraints=path_constraints,
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
    path_constraints: Optional[List[SMTTerm]] = None,
    debug: bool = False,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_optimization: bool = False,
    cache: Optional["RangeQueryCache"] = None,
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Solve for min/max values of a variable using SMT optimization.

    Args:
        solver: The SMT solver instance.
        smt_var: The tracked SMT variable to solve for.
        path_constraints: Optional list of path constraints to apply.
        debug: Enable debug output.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_optimization: If True, return type bounds without SMT solving.
        cache: Optional RangeQueryCache for memoization.

    Returns:
        Tuple of (min_result, max_result) dicts, or (None, None) on failure.
    """
    telemetry = get_telemetry()
    config = RangeQueryConfig(
        timeout_ms=timeout_ms, skip_optimization=skip_optimization, debug=debug
    )

    # Check cache first
    if cache is not None and not skip_optimization:
        var_id, constraints_tuple = _build_cache_key(smt_var, solver, path_constraints)
        cached_result = cache.get(var_id, constraints_tuple)
        if cached_result is not None:
            if telemetry:
                telemetry.count("cache_hit")
            return _unpack_cached_result(cached_result)
        if telemetry:
            telemetry.count("cache_miss")

    # Validate term is a bitvector
    if not solver.is_bitvector(smt_var.term):
        return None, None

    meta = _extract_variable_metadata(smt_var)
    if meta is None:
        return None, None

    if skip_optimization:
        if telemetry:
            telemetry.count("range_solve_skipped")
        return _get_fallback_range(meta)

    min_result, max_result = _solve_range_with_solver(
        solver, smt_var, meta, path_constraints, config, telemetry
    )

    if min_result is None or max_result is None:
        if telemetry:
            telemetry.count("range_solve_fallback")
        return _get_fallback_range(meta)

    if telemetry:
        telemetry.count("range_solve_success")

    # Store in cache
    if cache is not None:
        var_id, constraints_tuple = _build_cache_key(smt_var, solver, path_constraints)
        cache.put(var_id, constraints_tuple, min_result, max_result)

    return min_result, max_result


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
    """Run interval analysis on a function and return structured results.

    Args:
        function: The function to analyze.
        analysis: The interval analysis instance.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_range_solving: If True, skip SMT optimization and use type bounds.
        cache: Optional RangeQueryCache for memoization.
    """
    result = FunctionResult(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
    )

    if not function.nodes:
        result.error = "Function has no nodes"
        return result

    try:
        engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)
        engine.run_analysis()
        results: Dict[Node, AnalysisState[IntervalAnalysis]] = engine.result()

        solver = analysis.solver
        if not solver:
            result.error = "No solver available"
            return result

        # Process results - only collect from final nodes (return nodes or nodes with no successors)
        # Find return nodes (nodes with no sons)
        return_nodes = [node for node in function.nodes if not node.sons]
        if not return_nodes:
            # If no explicit return nodes, use the last node
            return_nodes = [function.nodes[-1]] if function.nodes else []

        # Check if return nodes are unreachable (BOTTOM/TOP variant)
        # If so, find the last node with STATE variant to get pre-revert state
        nodes_to_process = return_nodes
        all_unreachable = all(
            node not in results or results[node].post.variant != DomainVariant.STATE
            for node in return_nodes
        )
        if all_unreachable:
            # Find the last node with STATE variant (before the revert point)
            for node in reversed(function.nodes):
                if node in results and results[node].post.variant == DomainVariant.STATE:
                    nodes_to_process = [node]
                    break

        # Collect variables from selected nodes, filtering out temporary variables

        # First, identify return value variable names (TMPs that are returned)
        return_value_vars: set[str] = set()
        for node in function.nodes:
            for ir in node.irs:
                # Check for Return operations
                if type(ir).__name__ == "Return" and hasattr(ir, "values"):
                    for val in ir.values:
                        val_name = getattr(val, "name", None)
                        if val_name:
                            return_value_vars.add(val_name)

        for node in nodes_to_process:
            if node not in results:
                continue
            state = results[node]
            if state.post.variant == DomainVariant.STATE:
                post_state_vars: Dict[str, TrackedSMTVariable] = (
                    state.post.state.get_range_variables()
                )

                # Only show variables that were actually used
                used_vars = state.post.state.get_used_variables()
                for var_name, smt_var in post_state_vars.items():
                    # Filter out constants and most temporary variables
                    # But keep return value TMPs (they represent the function's output)
                    is_return_value = var_name in return_value_vars
                    if var_name.startswith("CONST_"):
                        continue
                    if var_name.startswith("TMP_") and not is_return_value:
                        continue
                    # Filter out REF_ variables (internal references)
                    if var_name.startswith("REF_"):
                        continue
                    # Filter out unused variables
                    if var_name not in used_vars:
                        continue
                    # Filter out global variables with unbounded ranges (not useful for analysis)
                    if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
                        continue

                    # Skip if we've already solved this exact variable
                    if var_name in result.variables:
                        continue

                    # Get path constraints from the domain state
                    path_constraints = state.post.state.get_path_constraints()
                    min_result, max_result = solve_variable_range(
                        solver,
                        smt_var,
                        path_constraints=path_constraints,
                        timeout_ms=timeout_ms,
                        skip_optimization=skip_range_solving,
                        cache=cache,
                    )

                    if min_result and max_result:
                        has_overflow = min_result.get("overflow", False) or max_result.get(
                            "overflow", False
                        )
                        is_wrapped = min_result["value"] > max_result["value"]

                        if is_wrapped:
                            range_str = f"[{max_result['value']}, {min_result['value']}]"
                        else:
                            range_str = f"[{min_result['value']}, {max_result['value']}]"

                        result.variables[var_name] = VariableResult(
                            name=var_name,
                            range_str=range_str,
                            overflow="YES" if has_overflow else "NO",
                            overflow_amount=max(
                                min_result.get("overflow_amount", 0),
                                max_result.get("overflow_amount", 0),
                            ),
                        )

    except Exception as e:
        # Log error with context, then stop execution
        from slither.analyses.data_flow.logger import get_logger, LogMessages

        logger = get_logger()
        logger.exception(
            LogMessages.ERROR_ANALYSIS_FAILED,
            error=str(e),
            function_name=function.name,
            embed_on_error=False,
        )
        raise

    return result


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
