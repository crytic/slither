"""Automated test suite for Slither data flow analysis."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
import sys

from rich.console import Console
from rich.table import Table

from slither import Slither
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import CheckSatResult
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from z3 import BitVecRef, Optimize, is_true, sat

if TYPE_CHECKING:
    from slither.analyses.data_flow.logger import DataFlowLogger, LogMessages

# Import expected results from separate file
from slither.analyses.data_flow.expected_results import EXPECTED_RESULTS

console = Console()


# =============================================================================
# DATA CLASSES FOR TEST RESULTS
# =============================================================================


@dataclass
class VariableResult:
    """Result for a single variable."""

    name: str
    range_str: str
    overflow: str
    overflow_amount: int = 0


@dataclass
class FunctionResult:
    """Result for a single function analysis."""

    function_name: str
    contract_name: str
    variables: Dict[str, VariableResult] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ContractResult:
    """Result for a single contract analysis."""

    contract_file: str
    contract_name: str
    functions: Dict[str, FunctionResult] = field(default_factory=dict)


@dataclass
class TestComparison:
    """Comparison result between expected and actual."""

    passed: bool
    variable_name: str
    expected_range: Optional[str] = None
    actual_range: Optional[str] = None
    expected_overflow: Optional[str] = None
    actual_overflow: Optional[str] = None
    message: str = ""


@dataclass
class FunctionTestResult:
    """Test result for a single function."""

    function_name: str
    passed: bool
    comparisons: List[TestComparison] = field(default_factory=list)
    missing_expected: List[str] = field(default_factory=list)
    unexpected_vars: List[str] = field(default_factory=list)


@dataclass
class ContractTestResult:
    """Test result for a single contract."""

    contract_file: str
    contract_name: str
    passed: bool
    function_results: Dict[str, FunctionTestResult] = field(default_factory=dict)
    error: Optional[str] = None


# =============================================================================
# SOLVER FUNCTIONS
# =============================================================================


def solve_variable_range(
    solver: object, smt_var: TrackedSMTVariable, debug: bool = False
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Solve for min/max values of a variable."""
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

    def _create_fresh_optimizer():
        opt = Optimize()
        opt.set("timeout", 2000)
        opt.set("opt.priority", "box")
        opt.set("opt.maxsat_engine", "wmax")

        if hasattr(solver, "solver"):
            z3_solver = solver.solver
            assertions = z3_solver.assertions()
            for assertion in assertions:
                opt.add(assertion)
        else:
            return None
        return opt

    def _optimize_range(maximize: bool) -> Optional[Dict]:
        try:
            opt = _create_fresh_optimizer()
            if opt is None:
                return None

            from z3 import is_bv

            objective = term if is_bv(term) else term

            if maximize:
                opt.maximize(objective)
            else:
                opt.minimize(objective)

            result = opt.check()
            if result != sat:
                return None

            z3_model = opt.model()
            if z3_model is None:
                return None

            value_term = z3_model.eval(term, model_completion=True)
            if hasattr(value_term, "as_long"):
                raw_value = value_term.as_long()
            else:
                return None

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
            return None

    try:
        base_result = solver.check_sat()
        if base_result != CheckSatResult.SAT:
            return None, None
    except Exception:
        pass

    min_result = _optimize_range(maximize=False)
    max_result = _optimize_range(maximize=True)
    return min_result, max_result


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================


def analyze_function_quiet(
    function: Function,
    analysis: IntervalAnalysis,
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

                    min_result, max_result = solve_variable_range(solver, smt_var)

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
        result.error = str(e)

    return result


def analyze_contract_quiet(contract_path: Path) -> List[ContractResult]:
    """Analyze a contract file and return structured results."""
    from slither.analyses.data_flow.smt_solver import Z3Solver

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

            for function in implemented_functions:
                solver = Z3Solver(use_optimizer=False)
                analysis = IntervalAnalysis(solver=solver)
                func_result = analyze_function_quiet(function, analysis)
                contract_result.functions[function.name] = func_result

            results.append(contract_result)

    except Exception as e:
        results.append(
            ContractResult(
                contract_file=contract_path.name,
                contract_name="ERROR",
                functions={
                    "_error": FunctionResult(
                        function_name="_error", contract_name="ERROR", error=str(e)
                    )
                },
            )
        )

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

    # Discover all .sol files
    sol_files = sorted(contracts_dir.glob("*.sol"))

    if not sol_files:
        console.print(f"[red]No .sol files found in {contracts_dir}[/red]")
        return 1

    total_contracts = 0
    passed_contracts = 0
    total_functions = 0
    passed_functions = 0

    contract_test_results: List[ContractTestResult] = []

    for sol_file in sol_files:
        if sol_file.name not in EXPECTED_RESULTS:
            if verbose:
                console.print(f"[dim]Skipping {sol_file.name} (no expected results defined)[/dim]")
            continue

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
    _display_test_results(contract_test_results, verbose)

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


def _display_test_results(results: List[ContractTestResult], verbose: bool) -> None:
    """Display test results with rich formatting."""
    for contract_test in results:
        passed_funcs = sum(1 for f in contract_test.function_results.values() if f.passed)
        total_funcs = len(contract_test.function_results)

        if contract_test.passed:
            console.print(
                f"[bold green]✓[/bold green] {contract_test.contract_file} - "
                f"[green]PASSED[/green] ({passed_funcs}/{total_funcs} functions)"
            )
        else:
            console.print(
                f"[bold red]✗[/bold red] {contract_test.contract_file} - "
                f"[red]FAILED[/red] ({passed_funcs}/{total_funcs} functions)"
            )

        # Show function details
        for func_name, func_test in contract_test.function_results.items():
            if func_test.passed:
                console.print(
                    f"  [green]✓[/green] {contract_test.contract_name}.{func_name} - All variables correct"
                )
            else:
                console.print(
                    f"  [red]✗[/red] {contract_test.contract_name}.{func_name} - Variable mismatch"
                )

                # Show mismatches
                for comparison in func_test.comparisons:
                    if not comparison.passed:
                        console.print(f"    [yellow]Variable:[/yellow] {comparison.variable_name}")
                        if comparison.expected_range != comparison.actual_range:
                            console.print(
                                f"      Expected range: [cyan]{comparison.expected_range}[/cyan]"
                            )
                            console.print(
                                f"      Got range:      [red]{comparison.actual_range}[/red]"
                            )
                        if comparison.expected_overflow != comparison.actual_overflow:
                            console.print(
                                f"      Expected overflow: [cyan]{comparison.expected_overflow}[/cyan]"
                            )
                            console.print(
                                f"      Got overflow:      [red]{comparison.actual_overflow}[/red]"
                            )

                # Show missing variables
                for missing in func_test.missing_expected:
                    console.print(f"    [red]Missing expected variable:[/red] {missing}")

                # Show unexpected variables (informational)
                if verbose and func_test.unexpected_vars:
                    for unexpected in func_test.unexpected_vars:
                        console.print(f"    [dim]Unexpected variable:[/dim] {unexpected}")


# =============================================================================
# VERBOSE OUTPUT MODE (Original functionality)
# =============================================================================


def _display_variable_ranges_table(variable_results: List[Dict]) -> None:
    """Display variable ranges in a formatted rich table."""
    if not variable_results:
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Variable", style="bold", justify="left")
    table.add_column("Range", justify="left")
    table.add_column("Overflow", justify="left")
    table.add_column("Overflow Amount", justify="left")

    for result in variable_results:
        var_name = result["name"]
        min_val = result["min"]
        max_val = result["max"]

        has_overflow = min_val.get("overflow", False) or max_val.get("overflow", False)
        is_wrapped = min_val["value"] > max_val["value"]

        if is_wrapped:
            range_str = f"[{max_val['value']}, {min_val['value']}] (wrapped)"
        else:
            range_str = f"[{min_val['value']}, {max_val['value']}]"

        range_style = "red" if has_overflow else "white"

        if has_overflow:
            overflow_str = "✗ YES"
            overflow_style = "red bold"
            min_overflow = min_val.get("overflow_amount", 0)
            max_overflow = max_val.get("overflow_amount", 0)
            if min_val.get("overflow", False) and max_val.get("overflow", False):
                amount_str = f"min: {min_overflow:+d}, max: {max_overflow:+d}"
            elif min_val.get("overflow", False):
                amount_str = f"min: {min_overflow:+d}"
            else:
                amount_str = f"max: {max_overflow:+d}"
        else:
            overflow_str = "✓ NO"
            overflow_style = "white"
            amount_str = "-"

        table.add_row(
            var_name,
            f"[{range_style}]{range_str}[/{range_style}]",
            f"[{overflow_style}]{overflow_str}[/{overflow_style}]",
            f"[{overflow_style}]{amount_str}[/{overflow_style}]",
        )

    console.print(table)


def analyze_function_verbose(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
    debug: bool = False,
) -> None:
    """Run interval analysis on a single function with verbose output."""
    logger.info(
        "Analyzing function: {function_name} ({signature})",
        function_name=function.name,
        signature=function.signature,
    )

    console.print(f"\n[bold blue]=== Function: {function.name} ===[/bold blue]")

    if not function.nodes:
        logger.warning(
            LogMessages.WARNING_SKIP_NODE,
            node_id="N/A",
            reason="function has no nodes (not implemented)",
        )
        return

    logger.info(LogMessages.ENGINE_INIT, function_name=function.name)
    engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)

    logger.debug(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")
    engine.run_analysis()

    results: Dict[Node, AnalysisState[IntervalAnalysis]] = engine.result()
    logger.info("Analysis complete! Processed {count} nodes.", count=len(results))

    for node, state in results.items():
        logger.debug(
            "Node {node_id} - Pre-state: {pre_state}, Post-state: {post_state}",
            node_id=node.node_id,
            pre_state=state.pre.variant,
            post_state=state.post.variant,
        )

        if state.post.variant == DomainVariant.STATE:
            post_state_vars: Dict[str, TrackedSMTVariable] = state.post.state.get_range_variables()

            if post_state_vars:
                node_code: str = ""
                if node.expression:
                    node_code = str(node.expression)
                elif hasattr(node, "source_mapping") and node.source_mapping:
                    node_code = node.source_mapping.content.strip()
                elif str(node):
                    node_code = str(node)

                if node_code:
                    console.print(f"\n[bold white]Code:[/bold white] [dim]{node_code}[/dim]")

                solver = analysis.solver
                if solver:
                    # Only show variables that were actually used
                    used_vars = state.post.state.get_used_variables()
                    variable_results: List[Dict] = []
                    for var_name, smt_var in sorted(post_state_vars.items()):
                        if var_name.startswith("CONST_"):
                            continue
                        # Filter out unused variables
                        if var_name not in used_vars:
                            continue

                        if debug:
                            console.print(f"\n[bold]Solving range for: {var_name}[/bold]")
                        min_result, max_result = solve_variable_range(solver, smt_var, debug=debug)

                        if min_result and max_result:
                            variable_results.append(
                                {
                                    "name": var_name,
                                    "sort": smt_var.sort,
                                    "min": min_result,
                                    "max": max_result,
                                }
                            )
                        else:
                            logger.debug(
                                "Could not solve range for variable {var_name}",
                                var_name=var_name,
                            )

                    if variable_results:
                        _display_variable_ranges_table(variable_results)
                    elif post_state_vars:
                        console.print(
                            "[yellow]Variables in state but could not solve ranges: "
                            f"{', '.join(sorted(post_state_vars.keys()))}[/yellow]"
                        )


def run_verbose(
    contract_path: str, debug: bool = False, function_name: Optional[str] = None
) -> None:
    """Run analysis with verbose output (original behavior).

    Args:
        contract_path: Path to the contract file
        debug: Enable debug output
        function_name: Optional function name to filter to (if None, shows all functions)
    """
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger
    from slither.analyses.data_flow.smt_solver import Z3Solver

    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="DEBUG")
    logger.info(LogMessages.ENGINE_START)

    logger.info("Loading contract from: {path}", path=contract_path)
    slither: Slither = Slither(contract_path)

    contracts: List[Contract]
    if slither.compilation_units:
        contracts = []
        for compilation_unit in slither.compilation_units:
            contracts.extend(compilation_unit.contracts)
    else:
        contracts = slither.contracts

    if not contracts:
        logger.warning("No contracts found!")
        return

    logger.info("Found {count} contract(s)", count=len(contracts))
    logger.info(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")

    for contract in contracts:
        logger.info("Processing contract: {contract_name}", contract_name=contract.name)

        functions: List[Function] = contract.functions_and_modifiers_declared
        implemented_functions: List[Function] = [
            f for f in functions if f.is_implemented and not f.is_constructor
        ]

        if function_name:
            implemented_functions = [f for f in implemented_functions if f.name == function_name]
            if not implemented_functions:
                console.print(
                    f"[yellow]Function '{function_name}' not found in contract '{contract.name}'[/yellow]"
                )
                continue

        if not implemented_functions:
            logger.warning(
                "No implemented functions found in {contract_name}", contract_name=contract.name
            )
            continue

        logger.info(
            "Found {count} implemented function(s) in {contract_name}",
            count=len(implemented_functions),
            contract_name=contract.name,
        )

        for function in implemented_functions:
            try:
                solver = Z3Solver(use_optimizer=False)
                analysis: IntervalAnalysis = IntervalAnalysis(solver=solver)
                analyze_function_verbose(function, analysis, logger, LogMessages, debug=debug)
            except Exception as e:
                logger.exception(
                    LogMessages.ERROR_ANALYSIS_FAILED,
                    error=str(e),
                    function_name=function.name,
                    embed_on_error=False,
                )

    logger.info(LogMessages.ENGINE_COMPLETE)


def generate_expected_results(contracts_dir: Path) -> None:
    """Generate expected results from current analysis output and save to expected_results.py."""
    console.print("\n[bold cyan]Generating expected results from current analysis...[/bold cyan]\n")

    # Discover all .sol files
    sol_files = sorted(contracts_dir.glob("*.sol"))

    if not sol_files:
        console.print(f"[red]No .sol files found in {contracts_dir}[/red]")
        return

    # Analyze all contracts
    all_results: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]] = {}

    for sol_file in sol_files:
        console.print(f"[dim]Analyzing {sol_file.name}...[/dim]")
        contract_results = analyze_contract_quiet(sol_file)

        for contract_result in contract_results:
            if contract_result.contract_name == "ERROR":
                console.print(f"[yellow]Skipping {sol_file.name} due to error[/yellow]")
                continue

            if sol_file.name not in all_results:
                all_results[sol_file.name] = {}

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

    for contract_file, contracts in sorted(all_results.items()):
        output_lines.append(f'    "{contract_file}": {{')
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
            f"\n[bold green]✓[/bold green] Expected results saved to: {expected_results_path}"
        )
    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] Failed to save expected results: {e}")
        return

    console.print("[dim]Note: Review and adjust the results as needed.[/dim]\n")


def show_test_output(
    contract_file: str, function_name: Optional[str] = None, contracts_dir: str = "../contracts/src"
) -> None:
    """Show verbose table output for a specific test contract/function.

    Args:
        contract_file: Name of the contract file (e.g., "FunctionArgs.sol")
        function_name: Optional function name to filter to
        contracts_dir: Directory containing contract files
    """
    contract_path = Path(contracts_dir) / contract_file
    if not contract_path.exists():
        console.print(f"[red]Contract file not found: {contract_path}[/red]")
        return

    console.print(f"[bold cyan]Showing verbose output for: {contract_file}[/bold cyan]")
    if function_name:
        console.print(f"[bold cyan]Function: {function_name}[/bold cyan]")
    console.print()

    # Suppress logger output, only show tables
    import logging

    # Set all loggers to ERROR level to suppress INFO/DEBUG
    logging.getLogger("slither").setLevel(logging.ERROR)
    logging.getLogger("slither.analyses.data_flow").setLevel(logging.ERROR)

    # Also suppress rich console output from logger
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger

    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="ERROR")

    run_verbose(str(contract_path), debug=False, function_name=function_name)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main() -> int:
    """Main entry point with command-line argument handling."""
    import argparse

    parser = argparse.ArgumentParser(description="Slither Data Flow Analysis Test Suite")
    parser.add_argument(
        "--test", "-t", action="store_true", help="Run automated tests against expected results"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run in verbose mode (original behavior) or show extra test details",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Show detailed debugging information"
    )
    parser.add_argument(
        "--contract",
        "-c",
        type=str,
        default="../contracts/src/FunctionArgs.sol",
        help="Path to contract file for verbose mode (default: ../contracts/src/FunctionArgs.sol)",
    )
    parser.add_argument(
        "--contracts-dir",
        type=str,
        default="../contracts/src",
        help="Directory containing .sol files for test mode (default: ../contracts/src)",
    )
    parser.add_argument(
        "--show",
        "-s",
        type=str,
        metavar="CONTRACT_FILE",
        help="Show verbose table output for a specific contract file (e.g., FunctionArgs.sol)",
    )
    parser.add_argument(
        "--function",
        "-f",
        type=str,
        metavar="FUNCTION_NAME",
        help="Filter to a specific function name (use with --show or --contract)",
    )
    parser.add_argument(
        "--generate-expected",
        "-g",
        action="store_true",
        help="Generate expected results from current analysis output (for copying into expected_results.py)",
    )

    args = parser.parse_args()

    if args.generate_expected:
        # Generate expected results from current analysis
        contracts_dir = Path(args.contracts_dir)
        if not contracts_dir.exists():
            console.print(f"[red]Contracts directory not found: {contracts_dir}[/red]")
            return 1
        generate_expected_results(contracts_dir)
        return 0
    elif args.show:
        # Show verbose output for a specific test
        show_test_output(args.show, function_name=args.function, contracts_dir=args.contracts_dir)
        return 0
    elif args.test:
        # Automated test mode
        contracts_dir = Path(args.contracts_dir)
        if not contracts_dir.exists():
            console.print(f"[red]Contracts directory not found: {contracts_dir}[/red]")
            return 1
        return run_tests(contracts_dir, verbose=args.verbose)
    else:
        # Verbose mode (original behavior)
        run_verbose(args.contract, debug=args.debug, function_name=args.function)
        return 0


if __name__ == "__main__":
    sys.exit(main())
