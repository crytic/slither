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
from slither.analyses.data_flow.display import console, display_test_results
from slither.analyses.data_flow.models import (
    VariableResult,
    FunctionResult,
    ContractResult,
    TestComparison,
    FunctionTestResult,
    ContractTestResult,
)
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from z3 import BitVecRef, Optimize, is_true, sat

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

# Import expected results from separate file
from slither.analyses.data_flow.expected_results import EXPECTED_RESULTS

# Default timeout for Optimize queries (milliseconds)
# Reduced from 2000ms to 500ms for faster analysis (4x speedup)
# Trade-off: Slightly less precise ranges, but much faster
# For very precise ranges, use --timeout 2000 or higher
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

    try:
        if telemetry:
            telemetry.count("check_sat_base")
        base_result = solver.check_sat()
        if base_result != CheckSatResult.SAT:
            # When path constraints are contradictory (e.g., both branch_taken=True/False),
            # fall back to type bounds instead of failing to produce a range.
            if telemetry:
                telemetry.count("range_solve_fallback_unsat")
            return _fallback_range()
    except Exception:
        pass

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

        # Collect variables only from return nodes, and filter out temporary variables
        for node in return_nodes:
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
                    # Filter out constants and temporary variables
                    if var_name.startswith("CONST_") or var_name.startswith("TMP_"):
                        continue
                    # Filter out unused variables
                    if var_name not in used_vars:
                        continue
                    # Filter out global variables with unbounded ranges (not useful for analysis)
                    if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
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
# TEST COMPARISON FUNCTIONS
# =============================================================================


def compare_function_results(
    expected: Dict[str, Dict[str, str]],
    actual: FunctionResult,
) -> FunctionTestResult:
    """Compare expected vs actual results for a function."""
    test_result = FunctionTestResult(
        function_name=actual.function_name,
        passed=True,
        comparisons=[],
        missing_expected=[],
        unexpected_vars=[],
    )

    expected_vars = expected.get("variables", {})
    actual_vars = actual.variables

    # Check each expected variable
    for var_name, expected_data in expected_vars.items():
        if var_name not in actual_vars:
            test_result.missing_expected.append(var_name)
            test_result.passed = False
            continue

        actual_var = actual_vars[var_name]
        comparison = TestComparison(
            passed=True,
            variable_name=var_name,
            expected_range=expected_data.get("range"),
            actual_range=actual_var.range_str,
            expected_overflow=expected_data.get("overflow"),
            actual_overflow=actual_var.overflow,
        )

        # Compare range
        if comparison.expected_range and comparison.expected_range != comparison.actual_range:
            comparison.passed = False
            comparison.message = "Range mismatch"
            test_result.passed = False

        # Compare overflow
        if (
            comparison.expected_overflow
            and comparison.expected_overflow != comparison.actual_overflow
        ):
            comparison.passed = False
            comparison.message = (
                comparison.message + " | Overflow mismatch"
                if comparison.message
                else "Overflow mismatch"
            )
            test_result.passed = False

        test_result.comparisons.append(comparison)

    # Check for unexpected variables (not in expected but in actual)
    for var_name in actual_vars:
        if var_name not in expected_vars:
            test_result.unexpected_vars.append(var_name)
            # Note: unexpected vars don't fail the test, just reported

    return test_result


def run_tests(contracts_dir: Path, verbose: bool = False) -> int:
    """Run all tests and return exit code (0=pass, 1=fail)."""
    console.print("\n[bold cyan]Running Slither data flow analysis tests...[/bold cyan]\n")

    # Only test files that are in EXPECTED_RESULTS
    expected_file_names = set(EXPECTED_RESULTS.keys())

    if not expected_file_names:
        console.print("[red]No expected results defined![/red]")
        return 1

    # Find matching .sol files
    sol_files = []
    for file_name in sorted(expected_file_names):
        sol_file = contracts_dir / file_name
        if sol_file.exists():
            sol_files.append(sol_file)
        elif verbose:
            console.print(
                f"[yellow]Warning: Expected file {file_name} not found in {contracts_dir}[/yellow]"
            )

    if not sol_files:
        console.print(f"[red]No matching .sol files found in {contracts_dir}[/red]")
        console.print(f"[dim]Expected files: {', '.join(sorted(expected_file_names))}[/dim]")
        return 1

    if verbose:
        console.print(f"[dim]Testing {len(sol_files)} file(s) with expected results[/dim]\n")

    total_contracts = 0
    passed_contracts = 0
    total_functions = 0
    passed_functions = 0

    contract_test_results: List[ContractTestResult] = []

    for sol_file in sol_files:
        expected_contract_data = EXPECTED_RESULTS[sol_file.name]

        # Analyze the contract
        contract_results = analyze_contract_quiet(sol_file)

        for contract_result in contract_results:
            if contract_result.contract_name not in expected_contract_data:
                continue

            total_contracts += 1
            expected_functions = expected_contract_data[contract_result.contract_name]

            contract_test = ContractTestResult(
                contract_file=sol_file.name,
                contract_name=contract_result.contract_name,
                passed=True,
            )

            for func_name, expected_func_data in expected_functions.items():
                total_functions += 1

                if func_name not in contract_result.functions:
                    contract_test.function_results[func_name] = FunctionTestResult(
                        function_name=func_name,
                        passed=False,
                        comparisons=[],
                        missing_expected=["Function not found in analysis"],
                    )
                    contract_test.passed = False
                    continue

                actual_func = contract_result.functions[func_name]
                func_test = compare_function_results(expected_func_data, actual_func)
                contract_test.function_results[func_name] = func_test

                if func_test.passed:
                    passed_functions += 1
                else:
                    contract_test.passed = False

            if contract_test.passed:
                passed_contracts += 1

            contract_test_results.append(contract_test)

    # Display results
    display_test_results(contract_test_results, verbose)

    # Summary
    console.print("\n" + "=" * 50)
    console.print(f"[bold]Results:[/bold] {total_contracts} contracts tested")
    console.print(
        f"[bold green]Passed:[/bold green] {passed_contracts} | "
        f"[bold red]Failed:[/bold red] {total_contracts - passed_contracts}"
    )
    console.print(f"[bold]Functions tested:[/bold] {total_functions}")
    console.print(
        f"[bold green]Passed:[/bold green] {passed_functions} | "
        f"[bold red]Failed:[/bold red] {total_functions - passed_functions}"
    )
    console.print("=" * 50)

    return 0 if passed_contracts == total_contracts else 1


# =============================================================================
# EXPECTED RESULTS GENERATION
# =============================================================================


def generate_expected_results(contracts_dir: Path, contract_file: Optional[str] = None) -> None:
    """Generate expected results from current analysis output and save to expected_results.py.

    Args:
        contracts_dir: Directory containing contract files
        contract_file: Optional contract file name (e.g., "FunctionArgs.sol"). If provided,
                      only generates results for this file and merges with existing results.
    """
    if contract_file:
        console.print(
            f"\n[bold cyan]Generating expected results for {contract_file}...[/bold cyan]\n"
        )
    else:
        console.print(
            "\n[bold cyan]Generating expected results from current analysis...[/bold cyan]\n"
        )

    # Load existing results if updating a single file
    all_results: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]] = {}
    was_already_present = False
    if contract_file:
        try:
            from slither.analyses.data_flow.expected_results import EXPECTED_RESULTS

            all_results = EXPECTED_RESULTS.copy()
            was_already_present = contract_file in all_results
            if was_already_present:
                console.print(
                    f"[yellow]![/yellow] [dim]{contract_file} already exists in expected results. Will update it.[/dim]"
                )
            else:
                console.print(
                    f"[green]V[/green] [dim]{contract_file} not found in expected results. Will add it.[/dim]"
                )
            console.print(
                f"[dim]Loaded existing results for {len(all_results)} contract file(s)[/dim]"
            )
        except Exception as e:
            console.print(f"[yellow]Could not load existing results: {e}[/yellow]")
            console.print("[dim]Will generate new results file[/dim]")

    # Discover .sol files to process
    if contract_file:
        # Process only the specified file
        sol_file = contracts_dir / contract_file
        if not sol_file.exists():
            console.print(f"[red]Contract file not found: {sol_file}[/red]")
            return
        sol_files = [sol_file]
    else:
        # Process all .sol files
        sol_files = sorted(contracts_dir.glob("*.sol"))
        if not sol_files:
            console.print(f"[red]No .sol files found in {contracts_dir}[/red]")
            return

    # Analyze contracts
    updated_contracts: List[str] = []
    added_contracts: List[str] = []

    for sol_file in sol_files:
        console.print(f"[dim]Analyzing {sol_file.name}...[/dim]")
        contract_results = analyze_contract_quiet(sol_file)

        for contract_result in contract_results:
            if contract_result.contract_name == "ERROR":
                console.print(f"[yellow]Skipping {sol_file.name} due to error[/yellow]")
                continue

            # Track if this is new or updated
            is_new = sol_file.name not in all_results
            if is_new:
                all_results[sol_file.name] = {}
                added_contracts.append(sol_file.name)
            elif contract_file and sol_file.name == contract_file:
                updated_contracts.append(sol_file.name)

            contract_data: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}

            for func_name, func_result in contract_result.functions.items():
                if func_result.error:
                    console.print(
                        f"[yellow]Skipping {func_name} due to error: {func_result.error}[/yellow]"
                    )
                    continue

                variables: Dict[str, Dict[str, str]] = {}
                for var_name, var_result in sorted(func_result.variables.items()):
                    variables[var_name] = {
                        "range": var_result.range_str,
                        "overflow": var_result.overflow,
                    }

                contract_data[func_name] = {"variables": variables}

            all_results[sol_file.name][contract_result.contract_name] = contract_data

    # Generate Python code as string
    output_lines = [
        '"""Expected results for automated data flow analysis tests.',
        "",
        "Format: contract_file -> contract_name -> function_name -> variables",
        'Each variable has: range (as "[min, max]"), overflow ("YES"/"NO")',
        '"""',
        "",
        "from typing import Dict",
        "",
        "EXPECTED_RESULTS: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = {",
    ]

    for contract_file_name, contracts in sorted(all_results.items()):
        output_lines.append(f'    "{contract_file_name}": {{')
        for contract_name, functions in sorted(contracts.items()):
            output_lines.append(f'        "{contract_name}": {{')
            for func_name, func_data in sorted(functions.items()):
                output_lines.append(f'            "{func_name}": {{')
                output_lines.append('                "variables": {')

                variables = func_data.get("variables", {})
                if variables:
                    for var_name, var_data in sorted(variables.items()):
                        range_val = var_data.get("range", "[0, 0]")
                        overflow_val = var_data.get("overflow", "NO")
                        output_lines.append(
                            f'                    "{var_name}": {{"range": "{range_val}", "overflow": "{overflow_val}"}},'
                        )
                else:
                    output_lines.append("                    # No variables tracked")

                output_lines.append("                }")
                output_lines.append("            },")
            output_lines.append("        },")
        output_lines.append("    },")

    output_lines.append("}")

    # Write to file
    expected_results_path = Path(__file__).parent / "expected_results.py"
    output_content = "\n".join(output_lines) + "\n"

    try:
        expected_results_path.write_text(output_content, encoding="utf-8")
        console.print(
            f"\n[bold green]V[/bold green] Expected results saved to: {expected_results_path}"
        )

        # Show summary of what was added/updated
        if contract_file:
            if updated_contracts:
                console.print(f"[green]Updated:[/green] {', '.join(updated_contracts)}")
            if added_contracts:
                console.print(f"[green]Added:[/green] {', '.join(added_contracts)}")
        else:
            if added_contracts:
                console.print(
                    f"[green]Generated results for {len(added_contracts)} contract file(s)[/green]"
                )
    except Exception as e:
        console.print(f"\n[bold red]X[/bold red] Failed to save expected results: {e}")
        return

    console.print("[dim]Note: Review and adjust the results as needed.[/dim]\n")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    from slither.analyses.data_flow.cli import main

    sys.exit(main())
