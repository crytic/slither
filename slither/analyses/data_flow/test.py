from typing import Dict, List, Optional, TYPE_CHECKING

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

console = Console()


def solve_variable_range(
    solver: object, smt_var: TrackedSMTVariable, debug: bool = False
) -> tuple[Optional[Dict], Optional[Dict]]:
    """
    Solve for minimum and maximum values of a variable.

    Strategy: Create fresh optimizer instances for each query to avoid
    conflicts between multiple objectives.

    Returns:
        Tuple of (min_result, max_result) dictionaries with 'value' and 'overflow' keys
    """
    term = smt_var.term
    if not isinstance(term, BitVecRef):
        console.print(f"[yellow]Warning: {smt_var.name} is not a bitvector[/yellow]")
        return None, None

    metadata = getattr(smt_var.base, "metadata", {})
    is_signed = bool(metadata.get("is_signed", False))
    bit_width = metadata.get("bit_width")
    sort_parameters = getattr(smt_var.sort, "parameters", None)
    if bit_width is None and sort_parameters:
        bit_width = sort_parameters[0]

    if debug:
        console.print(
            f"\n[cyan]Solving range for {smt_var.name} (signed={is_signed}, width={bit_width})[/cyan]"
        )

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
        """Create a new optimizer with all current constraints."""
        opt = Optimize()

        # Set a shorter timeout to prevent hanging (5 seconds)
        # For uint256, optimization should be fast with bitvectors
        opt.set("timeout", 2000)

        # Enable faster optimization strategies for bitvectors
        # These settings help Z3 optimize bitvectors more efficiently
        opt.set("opt.priority", "box")
        opt.set("opt.maxsat_engine", "wmax")

        # Copy all constraints from the original solver
        if hasattr(solver, "solver"):
            z3_solver = solver.solver
            assertions = z3_solver.assertions()
            if debug:
                console.print(f"[dim]Copying {len(assertions)} constraints to optimizer[/dim]")

                # Debug: Print first few assertions
                for i, assertion in enumerate(assertions[:5]):
                    console.print(f"[dim]  Constraint {i}: {assertion}[/dim]")
                if len(assertions) > 5:
                    console.print(f"[dim]  ... and {len(assertions) - 5} more[/dim]")

            for assertion in assertions:
                opt.add(assertion)
        else:
            if debug:
                console.print("[yellow]Warning: Could not access solver assertions[/yellow]")
            return None

        return opt

    def _optimize_range(maximize: bool) -> Optional[Dict]:
        """Solve for min or max value using a fresh optimizer."""
        try:
            if debug:
                console.print(
                    f"[dim]Creating optimizer for {'max' if maximize else 'min'}...[/dim]"
                )
            opt = _create_fresh_optimizer()
            if opt is None:
                return None

            # Optimize all bitvectors directly without conversion
            # Z3 Optimize handles bitvectors natively and efficiently
            # Converting to integers (BV2Int) creates huge constraint formulas that slow down optimization
            # Since we use 256-bit bitvectors for all types, we can optimize them directly
            from z3 import is_bv

            if is_bv(term):
                # Optimize bitvector directly - Z3 handles this efficiently
                # This avoids the expensive BV2Int conversion which creates huge integer constraints
                objective = term
            else:
                # Not a bitvector, use as-is
                objective = term

            if debug:
                console.print(
                    f"[dim]Adding objective: {'maximize' if maximize else 'minimize'} {objective}[/dim]"
                )

            if maximize:
                opt.maximize(objective)
            else:
                opt.minimize(objective)

            # Check satisfiability
            if debug:
                console.print(f"[dim]Checking satisfiability...[/dim]")
            result = opt.check()
            if debug:
                console.print(f"[dim]Result: {result}[/dim]")

            if result != sat:
                if debug:
                    console.print(f"[red]Optimization returned {result}[/red]")
                return None

            # Get the model
            z3_model = opt.model()
            if z3_model is None:
                if debug:
                    console.print("[red]Model is None[/red]")
                return None

            # Evaluate the term
            value_term = z3_model.eval(term, model_completion=True)
            if debug:
                console.print(f"[dim]Evaluated term: {value_term}[/dim]")

            if hasattr(value_term, "as_long"):
                raw_value = value_term.as_long()
            else:
                if debug:
                    console.print("[red]Cannot convert value to long[/red]")
                return None

            wrapped_value = _decode_model_value(raw_value)
            if debug:
                console.print(
                    f"[green]{'Max' if maximize else 'Min'} value: {wrapped_value}[/green]"
                )

            # Check overflow flag
            overflow = False
            try:
                flag_term = z3_model.eval(smt_var.overflow_flag.term, model_completion=True)
                overflow = is_true(flag_term)
                if debug:
                    console.print(f"[dim]Overflow flag: {overflow}[/dim]")
            except Exception as e:
                if debug:
                    console.print(f"[yellow]Could not evaluate overflow flag: {e}[/yellow]")

            # Check overflow amount
            overflow_amount = 0
            try:
                amount_term = z3_model.eval(smt_var.overflow_amount.term, model_completion=True)
                if hasattr(amount_term, "as_long"):
                    overflow_amount = amount_term.as_long()
                if debug:
                    console.print(f"[dim]Overflow amount: {overflow_amount}[/dim]")
            except Exception as e:
                if debug:
                    console.print(f"[yellow]Could not evaluate overflow amount: {e}[/yellow]")

            return {
                "value": wrapped_value,
                "overflow": overflow,
                "overflow_amount": overflow_amount,
            }
        except Exception as e:
            if debug:
                console.print(f"[red]Error in _optimize_range: {e}[/red]")
                import traceback

                traceback.print_exc()
            return None

    # First check if base constraints are satisfiable
    if debug:
        console.print("[dim]Checking if base constraints are satisfiable...[/dim]")

    # Print all constraints
    if debug and hasattr(solver, "solver"):
        z3_solver = solver.solver
        assertions = z3_solver.assertions()
        console.print(f"[yellow]Total constraints in solver: {len(assertions)}[/yellow]")
        console.print("[yellow]All constraints:[/yellow]")
        for i, assertion in enumerate(assertions):
            console.print(f"[yellow]  {i}: {assertion}[/yellow]")

    try:
        base_result = solver.check_sat()
        if debug:
            console.print(f"[dim]Base constraints: {base_result}[/dim]")
        if base_result != CheckSatResult.SAT:
            if debug:
                console.print(f"[red]Base constraints are {base_result}![/red]")

                # Try to get unsat core if available
                if hasattr(solver, "solver") and hasattr(solver.solver, "unsat_core"):
                    try:
                        core = solver.solver.unsat_core()
                        console.print(f"[red]UNSAT core ({len(core)} constraints):[/red]")
                        for constraint in core:
                            console.print(f"[red]  - {constraint}[/red]")
                    except Exception as e:
                        console.print(f"[yellow]Could not get unsat core: {e}[/yellow]")

            return None, None
    except Exception as e:
        if debug:
            console.print(f"[red]Error checking base satisfiability: {e}[/red]")

    # Solve for minimum
    min_result = _optimize_range(maximize=False)

    # Solve for maximum
    max_result = _optimize_range(maximize=True)

    return min_result, max_result


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

        # Check if overflow occurs
        has_overflow = min_val.get("overflow", False) or max_val.get("overflow", False)

        # Check for wrapped ranges
        is_wrapped = min_val["value"] > max_val["value"]

        # Format range
        if is_wrapped:
            range_str = f"[{max_val['value']}, {min_val['value']}] (wrapped)"
        else:
            range_str = f"[{min_val['value']}, {max_val['value']}]"

        # Styling
        range_style = "red" if has_overflow else "white"

        if has_overflow:
            overflow_str = "✗ YES"
            overflow_style = "red bold"

            # Calculate overflow amount details
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


def analyze_function(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
    debug: bool = False,
) -> None:
    """Run interval analysis on a single function."""
    logger.info(
        "Analyzing function: {function_name} ({signature})",
        function_name=function.name,
        signature=function.signature,
    )

    # Display function header with rich formatting
    console.print(f"\n[bold blue]=== Function: {function.name} ===[/bold blue]")

    # Skip if function has no nodes (not implemented or abstract)
    if not function.nodes:
        logger.warning(
            LogMessages.WARNING_SKIP_NODE,
            node_id="N/A",
            reason="function has no nodes (not implemented)",
        )
        return

    # Create engine with the analysis and function
    logger.info(LogMessages.ENGINE_INIT, function_name=function.name)
    engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)

    # Run the analysis
    logger.debug(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")
    engine.run_analysis()

    # Get and display results
    results: Dict[Node, AnalysisState[IntervalAnalysis]] = engine.result()
    logger.info("Analysis complete! Processed {count} nodes.", count=len(results))

    # Display results for each node
    for node, state in results.items():
        logger.debug(
            "Node {node_id} - Pre-state: {pre_state}, Post-state: {post_state}",
            node_id=node.node_id,
            pre_state=state.pre.variant,
            post_state=state.post.variant,
        )

        # Print post-state variables
        if state.post.variant == DomainVariant.STATE:
            post_state_vars: Dict[str, TrackedSMTVariable] = state.post.state.get_range_variables()

            if post_state_vars:
                # Get node's source code representation using str(node.expression)
                node_code: str = ""
                if node.expression:
                    node_code = str(node.expression)
                elif hasattr(node, "source_mapping") and node.source_mapping:
                    node_code = node.source_mapping.content.strip()
                elif str(node):
                    node_code = str(node)

                # Display code line if available
                if node_code:
                    console.print(f"\n[bold white]Code:[/bold white] [dim]{node_code}[/dim]")

                # Solve for min/max values and display results in a table
                solver = analysis.solver
                if solver:
                    # Collect variable results - show ALL variables in post-state
                    variable_results: List[Dict] = []
                    for var_name, smt_var in sorted(post_state_vars.items()):
                        # Skip internal constant variables
                        if var_name.startswith("CONST_"):
                            continue

                        # Solve for min and max
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
                            # Even if solving fails, show the variable exists
                            logger.debug(
                                "Could not solve range for variable {var_name}",
                                var_name=var_name,
                            )

                    # Display results in a rich table
                    if variable_results:
                        _display_variable_ranges_table(variable_results)
                    elif post_state_vars:
                        # Show that variables exist but couldn't be solved
                        console.print(
                            "[yellow]Variables in state but could not solve ranges: "
                            f"{', '.join(sorted(post_state_vars.keys()))}[/yellow]"
                        )


def main(debug: bool = False) -> None:
    # Import logger after Slither is loaded to avoid circular import issues
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger

    # Initialize logger
    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="DEBUG")
    logger.info(LogMessages.ENGINE_START)

    # Load the Solidity contract
    contract_path: str = "../contracts/src/Require.sol"
    logger.info("Loading contract from: {path}", path=contract_path)
    slither: Slither = Slither(contract_path)

    # Get all contracts - try compilation_units first, then fall back to contracts
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

    # We instantiate a fresh solver per function to avoid leaking constraints
    from slither.analyses.data_flow.smt_solver import Z3Solver

    logger.info(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")

    # Analyze all contracts and functions
    for contract in contracts:
        logger.info("Processing contract: {contract_name}", contract_name=contract.name)

        # Get all functions (including modifiers if needed)
        functions: List[Function] = contract.functions_and_modifiers_declared

        # Filter to only implemented, non-constructor functions
        implemented_functions: List[Function] = [
            f for f in functions if f.is_implemented and not f.is_constructor
        ]

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

        # Analyze each function
        for function in implemented_functions:
            try:
                # Fresh solver/analysis for every function execution
                solver = Z3Solver(use_optimizer=False)
                analysis: IntervalAnalysis = IntervalAnalysis(solver=solver)
                analyze_function(function, analysis, logger, LogMessages, debug=debug)
            except Exception as e:
                logger.exception(
                    LogMessages.ERROR_ANALYSIS_FAILED,
                    error=str(e),
                    function_name=function.name,
                    embed_on_error=False,
                )

    logger.info(LogMessages.ENGINE_COMPLETE)


if __name__ == "__main__":
    DEBUG = False  # Set to True to show detailed debugging information
    main(debug=DEBUG)
