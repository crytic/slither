"""Core test functions for Slither data flow analysis."""

from contextlib import nullcontext as _null_context
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
import sys

from slither import Slither
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import CheckSatResult
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.display import console
from slither.analyses.data_flow.models import (
    VariableResult,
    FunctionResult,
    ContractResult,
)
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from z3 import BitVecRef, Optimize, is_true, sat

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

# Default timeout for Optimize queries (milliseconds)
# 500ms is needed for correct results on 256-bit inequality constraints.
# For faster but less precise results, use --timeout 100 or lower.
DEFAULT_OPTIMIZE_TIMEOUT_MS = 500


# =============================================================================
# SOLVER FUNCTIONS
# =============================================================================


def solve_variable_range(
    solver: object,
    smt_var: TrackedSMTVariable,
    path_constraints: Optional[List] = None,
    debug: bool = False,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_optimization: bool = False,
    cache: Optional["RangeQueryCache"] = None,
    optimizer: Optional["Optimize"] = None,
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Solve for min/max values of a variable with optional path constraints.

    Args:
        solver: The SMT solver instance.
        smt_var: The tracked SMT variable to solve for.
        path_constraints: Optional list of path constraints to apply.
        debug: Enable debug output.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_optimization: If True, skip SMT optimization and return type bounds directly.
        cache: Optional RangeQueryCache for memoization.
        optimizer: Optional reusable Optimize instance (if None, creates fresh instances).

    Returns:
        Tuple of (min_result, max_result) dictionaries, or (None, None) on failure.
    """
    telemetry = get_telemetry()

    # Check cache first if available
    if cache is not None and not skip_optimization:
        # Build cache key from variable ID and constraints
        var_id = str(smt_var.term)
        constraint_strs = []

        # Include path constraints
        if path_constraints:
            constraint_strs.extend(str(c) for c in path_constraints)

        # Include global solver assertions
        if hasattr(solver, "solver"):
            z3_solver = solver.solver
            if hasattr(z3_solver, "assertions"):
                constraint_strs.extend(str(a) for a in z3_solver.assertions())

        constraints_tuple = tuple(constraint_strs)
        cached_result = cache.get(var_id, constraints_tuple)

        if cached_result is not None:
            if telemetry:
                telemetry.count("cache_hit")
            min_val, max_val = cached_result

            # Reconstruct result dictionaries from cached values
            if min_val is None or max_val is None:
                return None, None

            min_result = {
                "value": min_val.get("value") if isinstance(min_val, dict) else min_val,
                "overflow": min_val.get("overflow", False) if isinstance(min_val, dict) else False,
                "overflow_amount": (
                    min_val.get("overflow_amount", 0) if isinstance(min_val, dict) else 0
                ),
            }
            max_result = {
                "value": max_val.get("value") if isinstance(max_val, dict) else max_val,
                "overflow": max_val.get("overflow", False) if isinstance(max_val, dict) else False,
                "overflow_amount": (
                    max_val.get("overflow_amount", 0) if isinstance(max_val, dict) else 0
                ),
            }
            return min_result, max_result

        if telemetry:
            telemetry.count("cache_miss")

    term = smt_var.term
    if not isinstance(term, BitVecRef):
        return None, None

    metadata = getattr(smt_var.base, "metadata", {})
    is_signed = bool(metadata.get("is_signed", False))
    bit_width = metadata.get("bit_width")
    sort_parameters = getattr(smt_var.sort, "parameters", None)
    if bit_width is None and sort_parameters:
        bit_width = sort_parameters[0]

    min_bound = metadata.get("min_value")
    max_bound = metadata.get("max_value")

    def _decode_model_value(raw_value: int) -> int:
        width = bit_width if isinstance(bit_width, int) else 256
        mask = (1 << width) - 1 if width < 256 else (1 << 256) - 1
        value = raw_value & mask
        if is_signed and width > 0:
            half_range = 1 << (width - 1)
            if value >= half_range:
                value -= 1 << width
        if min_bound is not None:
            value = max(min_bound, value)
        if max_bound is not None:
            value = min(max_bound, value)
        return value

    def _get_optimizer_for_query():
        """Get an optimizer for the query, either reusing provided one or creating fresh."""
        # Early return: if reusable optimizer provided, use push/pop pattern
        if optimizer is not None:
            # CRITICAL: Set timeout on reused optimizer too!
            optimizer.set("timeout", timeout_ms)
            if telemetry:
                telemetry.count("optimize_instance_reused")
            return optimizer, True  # True = needs pop after use

        # Otherwise, create fresh optimizer (legacy path)
        if telemetry:
            telemetry.count("optimize_instance_created")

        opt = Optimize()
        opt.set("timeout", timeout_ms)
        opt.set("opt.priority", "box")
        opt.set("opt.maxsat_engine", "wmax")

        # Early return: check solver has assertions
        if not hasattr(solver, "solver"):
            return None, False

        # Add global solver assertions
        z3_solver = solver.solver
        assertions = z3_solver.assertions()
        assertion_count = 0
        for assertion in assertions:
            opt.add(assertion)
            assertion_count += 1

        if telemetry:
            telemetry.count("assertions_copied", assertion_count)

        # Add path-specific constraints
        if path_constraints:
            for constraint in path_constraints:
                opt.add(constraint)
            if telemetry:
                telemetry.count("path_constraints_added", len(path_constraints))

        return opt, False  # False = no pop needed

    def _fallback_range() -> tuple[Optional[Dict], Optional[Dict]]:
        """Return a conservative range using type bounds when optimization fails."""
        # Guard: need bit width to build a range
        if bit_width is None:
            return None, None

        # Compute default min/max from bit width and signedness
        unsigned_min = 0
        unsigned_max = (1 << bit_width) - 1
        signed_min = -(1 << (bit_width - 1))
        signed_max = (1 << (bit_width - 1)) - 1

        # Choose bounds based on signedness
        fallback_min = signed_min if is_signed else unsigned_min
        fallback_max = signed_max if is_signed else unsigned_max

        # Override with explicit type bounds when available
        if min_bound is not None:
            fallback_min = min_bound
        if max_bound is not None:
            fallback_max = max_bound

        min_result = {
            "value": fallback_min,
            "overflow": False,
            "overflow_amount": 0,
        }
        max_result = {
            "value": fallback_max,
            "overflow": False,
            "overflow_amount": 0,
        }
        return min_result, max_result

    def _optimize_range(maximize: bool) -> Optional[Dict]:
        op_name = "optimize_max" if maximize else "optimize_min"

        if telemetry:
            telemetry.count(op_name)

        opt, needs_pop = _get_optimizer_for_query()

        # Early return: no optimizer available
        if opt is None:
            return None

        try:
            with telemetry.time(op_name) if telemetry else _null_context():
                # Push new context if reusing optimizer
                if needs_pop:
                    opt.push()
                    if telemetry:
                        telemetry.count("push_pop_used")

                    # Add path constraints in the pushed context
                    if path_constraints:
                        for constraint in path_constraints:
                            opt.add(constraint)
                        if telemetry:
                            telemetry.count("path_constraints_added", len(path_constraints))

                from z3 import is_bv, BitVecVal

                objective = term if is_bv(term) else term

                # For signed types, use sign-bit XOR trick to convert signed order to unsigned order
                # This stays entirely in bitvector theory (no BV2Int), avoiding theory mixing overhead
                # XOR with sign bit maps: -128->0, -1->127, 0->128, 127->255 (for int8)
                # So signed ordering becomes unsigned ordering, and we can use standard min/max
                if is_signed and is_bv(objective):
                    width = bit_width if isinstance(bit_width, int) else 256
                    sign_bit = BitVecVal(1 << (width - 1), width)
                    objective = objective ^ sign_bit

                if maximize:
                    opt.maximize(objective)
                else:
                    opt.minimize(objective)

                result = opt.check()
                if telemetry:
                    telemetry.count("optimize_check")

                # Early return: check failed
                if result != sat:
                    if debug:
                        console.print(
                            f"[yellow]Optimize check returned {result} "
                            f"(reason: {opt.reason_unknown()}) for {'max' if maximize else 'min'}[/yellow]"
                        )
                    return None

                z3_model = opt.model()

                # Early return: no model
                if z3_model is None:
                    if debug:
                        console.print("[yellow]Optimize produced no model[/yellow]")
                    return None

                value_term = z3_model.eval(term, model_completion=True)

                # Early return: cannot extract value
                if not hasattr(value_term, "as_long"):
                    return None

                raw_value = value_term.as_long()
                wrapped_value = _decode_model_value(raw_value)

                overflow = False
                try:
                    flag_term = z3_model.eval(smt_var.overflow_flag.term, model_completion=True)
                    overflow = is_true(flag_term)
                except Exception:
                    pass

                overflow_amount = 0
                try:
                    amount_term = z3_model.eval(smt_var.overflow_amount.term, model_completion=True)
                    if hasattr(amount_term, "as_long"):
                        overflow_amount = amount_term.as_long()
                except Exception:
                    pass

                return {
                    "value": wrapped_value,
                    "overflow": overflow,
                    "overflow_amount": overflow_amount,
                }
        except Exception:
            if debug:
                console.print(
                    f"[yellow]Exception during optimize {'max' if maximize else 'min'}; returning None[/yellow]"
                )
            return None
        finally:
            # Pop context if we pushed one
            if needs_pop:
                opt.pop()

    # If skip_optimization is set, return conservative type bounds immediately
    if skip_optimization:
        if telemetry:
            telemetry.count("range_solve_skipped")
        return _fallback_range()

    # Skip base satisfiability check entirely - it's redundant.
    # The optimizer will fail fast (50ms timeout) if constraints are UNSAT/complex.
    # Previously this check was called 366 times with the SAME solver state,
    # wasting 30+ seconds on repeated timeout checks.
    # If optimizer fails, we fall back to type bounds anyway (lines below).

    min_result = _optimize_range(maximize=False)
    max_result = _optimize_range(maximize=True)

    if min_result is None or max_result is None:
        if debug:
            console.print(
                "[yellow]Range solve fallback: "
                f"min_result={min_result}, max_result={max_result}, "
                f"bit_width={bit_width}, is_signed={is_signed}, "
                f"path_constraints={path_constraints}[/yellow]"
            )
        # Fallback to conservative static bounds when optimization fails
        if telemetry:
            telemetry.count("range_solve_fallback_opt_failed")
        return _fallback_range()

    if telemetry:
        telemetry.count("range_solve_success")

    # Store result in cache if available
    if cache is not None:
        var_id = str(smt_var.term)
        constraint_strs = []
        if path_constraints:
            constraint_strs.extend(str(c) for c in path_constraints)
        if hasattr(solver, "solver"):
            z3_solver = solver.solver
            if hasattr(z3_solver, "assertions"):
                constraint_strs.extend(str(a) for a in z3_solver.assertions())
        constraints_tuple = tuple(constraint_strs)
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
    optimizer: Optional["Optimize"] = None,
) -> FunctionResult:
    """Run interval analysis on a function and return structured results.

    Args:
        function: The function to analyze.
        analysis: The interval analysis instance.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_range_solving: If True, skip SMT optimization and use type bounds.
        cache: Optional RangeQueryCache for memoization.
        optimizer: Optional reusable Optimize instance.
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
                        optimizer=optimizer,
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

            # Create shared cache and optimizer for all functions in this contract
            cache = RangeQueryCache(max_size=1000)

            for function in implemented_functions:
                solver = Z3Solver(use_optimizer=True)
                analysis = IntervalAnalysis(solver=solver)

                # Get the optimizer from the solver for reuse
                optimizer = solver.solver if hasattr(solver, "solver") else None

                func_result = analyze_function_quiet(
                    function,
                    analysis,
                    timeout_ms=timeout_ms,
                    skip_range_solving=skip_range_solving,
                    cache=cache,
                    optimizer=optimizer,
                )
                contract_result.functions[function.name] = func_result

            results.append(contract_result)

    except Exception as e:
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
