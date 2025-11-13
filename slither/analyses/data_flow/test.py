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

if TYPE_CHECKING:
    from slither.analyses.data_flow.logger import DataFlowLogger, LogMessages

console = Console()


def solve_variable_range(
    solver: object, smt_var: TrackedSMTVariable
) -> tuple[Optional[Dict], Optional[Dict]]:
    """
    Solve for minimum and maximum values of a variable.

    Returns:
        Tuple of (min_result, max_result) dictionaries with 'value' and 'overflow' keys
    """
    from z3 import BitVecRef, BV2Int, is_true

    term = smt_var.term
    if not isinstance(term, BitVecRef):
        return None, None

    def _optimize_range(maximize: bool) -> Optional[Dict]:
        try:
            solver.push()
            objective = BV2Int(term)
            if maximize:
                solver.maximize(objective)
            else:
                solver.minimize(objective)
            if solver.check_sat() != CheckSatResult.SAT:
                return None
            model = solver.get_model()
            if not model or smt_var.name not in model:
                return None
            value_term = model[smt_var.name]
            if hasattr(value_term, "as_long"):
                wrapped_value = value_term.as_long()
            elif hasattr(value_term, "as_string"):
                try:
                    wrapped_value = int(value_term.as_string())
                except (ValueError, AttributeError):
                    wrapped_value = 0
            else:
                wrapped_value = 0

            overflow = False
            overflow_amount = 0
            if smt_var.overflow_flag.name in model:
                overflow = is_true(model[smt_var.overflow_flag.name])
            if smt_var.overflow_amount.name in model:
                amount_term = model[smt_var.overflow_amount.name]
                if hasattr(amount_term, "as_long"):
                    overflow_amount = amount_term.as_long()
                elif hasattr(amount_term, "as_string"):
                    try:
                        overflow_amount = int(amount_term.as_string())
                    except (ValueError, AttributeError):
                        overflow_amount = 0

            return {
                "value": wrapped_value,
                "overflow": overflow,
                "overflow_amount": overflow_amount,
            }
        finally:
            solver.pop()

    min_result = _optimize_range(maximize=False)
    max_result = _optimize_range(maximize=True)

    def _optimize_overflow_amount(maximize: bool) -> Optional[int]:
        try:
            solver.push()
            solver.assert_constraint(smt_var.overflow_flag.term)
            if maximize:
                solver.maximize(smt_var.overflow_amount.term)
            else:
                solver.minimize(smt_var.overflow_amount.term)
            if solver.check_sat() != CheckSatResult.SAT:
                return None
            model = solver.get_model()
            if not model or smt_var.overflow_amount.name not in model:
                return None
            amount_term = model[smt_var.overflow_amount.name]
            if hasattr(amount_term, "as_long"):
                return amount_term.as_long()
            if hasattr(amount_term, "as_string"):
                try:
                    return int(amount_term.as_string())
                except (ValueError, AttributeError):
                    return None
            return None
        finally:
            solver.pop()

    overflow_min_amount = _optimize_overflow_amount(maximize=False)
    overflow_max_amount = _optimize_overflow_amount(maximize=True)
    overflow_possible = overflow_min_amount is not None or overflow_max_amount is not None

    if overflow_possible:
        if min_result:
            min_result["overflow"] = True
            min_result["overflow_amount"] = (
                overflow_min_amount if overflow_min_amount is not None else 0
            )
        if max_result:
            max_result["overflow"] = True
            max_result["overflow_amount"] = (
                overflow_max_amount if overflow_max_amount is not None else 0
            )

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
                        min_result, max_result = solve_variable_range(solver, smt_var)

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


def main() -> None:
    # Import logger after Slither is loaded to avoid circular import issues
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger

    # Initialize logger
    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="INFO")
    logger.info(LogMessages.ENGINE_START)

    # Load the Solidity contract
    contract_path: str = "../contracts/src/Math.sol"
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

    # Create Z3 solver with optimizer for min/max queries
    from slither.analyses.data_flow.smt_solver import Z3Solver

    solver = Z3Solver(use_optimizer=True)

    # Create interval analysis with the solver (reuse for all functions)
    analysis: IntervalAnalysis = IntervalAnalysis(solver=solver)
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
                analyze_function(function, analysis, logger, LogMessages)
            except Exception as e:
                logger.exception(
                    LogMessages.ERROR_ANALYSIS_FAILED,
                    error=str(e),
                    function_name=function.name,
                    embed_on_error=False,
                )

    logger.info(LogMessages.ENGINE_COMPLETE)


if __name__ == "__main__":
    main()
