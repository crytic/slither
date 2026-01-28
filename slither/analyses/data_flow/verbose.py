"""Verbose mode analysis functions for data flow analysis."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from slither import Slither
from slither.exceptions import SlitherError
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.telemetry import (
    get_telemetry,
    enable_telemetry,
    reset_telemetry,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.display import (
    console,
    display_variable_ranges_table,
    display_safety_violations,
)
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function

if TYPE_CHECKING:
    from slither.analyses.data_flow.logger import DataFlowLogger, LogMessages
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache
    from z3 import Optimize


# Import DEFAULT_OPTIMIZE_TIMEOUT_MS from test module
DEFAULT_OPTIMIZE_TIMEOUT_MS = 10  # Aggressive timeout for display purposes


def analyze_function_verbose(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
    debug: bool = False,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_range_solving: bool = False,
    cache: Optional["RangeQueryCache"] = None,
    optimizer: Optional["Optimize"] = None,
) -> None:
    """Run interval analysis on a single function with verbose output organized by source line.

    Args:
        function: The function to analyze.
        analysis: The interval analysis instance.
        logger: The data flow logger.
        LogMessages: Log message constants class.
        debug: Enable debug output.
        timeout_ms: Timeout in milliseconds for each optimization query.
        skip_range_solving: If True, skip SMT optimization and use type bounds.
        cache: Optional RangeQueryCache for memoization.
        optimizer: Optional reusable Optimize instance.
    """
    # Import here to avoid circular imports
    from slither.analyses.data_flow.test import solve_variable_range

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

    # Group results by source line instead of processing node-by-node
    # This dramatically reduces duplicate range queries
    line_data: Dict[int, Dict] = defaultdict(
        lambda: {
            "code": None,
            "nodes": [],
            "variables": {},  # var_name -> (smt_var, constraints_tuple, state)
        }
    )

    for node, state in results.items():
        logger.debug(
            "Node {node_id} - Pre-state: {pre_state}, Post-state: {post_state}",
            node_id=node.node_id,
            pre_state=state.pre.variant,
            post_state=state.post.variant,
        )

        if state.post.variant != DomainVariant.STATE:
            continue

        post_state_vars: Dict[str, TrackedSMTVariable] = state.post.state.get_range_variables()
        if not post_state_vars:
            continue

        # Get source line(s) for this node
        lines = []
        if hasattr(node, "source_mapping") and node.source_mapping and node.source_mapping.lines:
            lines = node.source_mapping.lines

        # If no source mapping, create synthetic line number based on node_id
        if not lines:
            lines = [-node.node_id]  # Negative to distinguish from real lines

        # Get node code for display
        node_code: str = ""
        if node.expression:
            node_code = str(node.expression)
        elif hasattr(node, "source_mapping") and node.source_mapping:
            node_code = node.source_mapping.content.strip()
        elif str(node):
            node_code = str(node)

        # Add this node's data to each line it spans
        for line_num in lines:
            line_info = line_data[line_num]
            line_info["nodes"].append(node)

            # Store code (prefer non-empty)
            if node_code and not line_info["code"]:
                line_info["code"] = node_code

            # Get path constraints for deduplication
            path_constraints = state.post.state.get_path_constraints()
            constraints_tuple = tuple(str(c) for c in path_constraints)

            # Only show variables that were actually used
            used_vars = state.post.state.get_used_variables()

            for var_name, smt_var in post_state_vars.items():
                # Filter out constants, temporaries, and unused variables
                if (
                    var_name.startswith("CONST_")
                    or var_name.startswith("TMP_")
                    or var_name not in used_vars
                ):
                    continue
                # Filter out global variables with unbounded ranges (not useful for analysis)
                if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
                    continue

                # Deduplicate: only store unique (var_name, constraints) pairs
                var_key = (var_name, constraints_tuple)
                if var_key not in line_info["variables"]:
                    line_info["variables"][var_key] = (smt_var, path_constraints, state)

    # Now process each line in order and compute ranges once per unique variable state
    solver = analysis.solver
    if not solver:
        logger.warning("No solver available for range solving")
        return

    for line_num in sorted(line_data.keys()):
        line_info = line_data[line_num]

        if not line_info["variables"]:
            continue

        # Display the code for this line
        if line_info["code"]:
            console.print(f"\n[bold white]Code:[/bold white] [dim]{line_info['code']}[/dim]")

        # Compute ranges for unique variables at this line
        variable_results: List[Dict] = []
        for (var_name, constraints_tuple), (smt_var, path_constraints, state) in sorted(
            line_info["variables"].items(), key=lambda x: x[0][0]  # Sort by var_name
        ):
            if debug:
                console.print(f"\n[bold]Solving range for: {var_name}[/bold]")

            min_result, max_result = solve_variable_range(
                solver,
                smt_var,
                path_constraints=path_constraints,
                debug=debug,
                timeout_ms=timeout_ms,
                skip_optimization=skip_range_solving,
                cache=cache,
                optimizer=optimizer,
            )

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
            display_variable_ranges_table(variable_results)
        else:
            var_names = [var_name for var_name, _ in line_info["variables"].keys()]
            if var_names:
                console.print(
                    "[yellow]Variables in state but could not solve ranges: "
                    f"{', '.join(sorted(var_names))}[/yellow]"
                )

    # Display safety violations if any were detected
    display_safety_violations(analysis.safety_violations)


def run_verbose(
    contract_path: str,
    debug: bool = False,
    function_name: Optional[str] = None,
    contract_name: Optional[str] = None,
    embed: bool = False,
    skip_compile: bool = False,
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS,
    skip_range_solving: bool = False,
    show_telemetry: bool = False,
) -> None:
    """Run analysis with verbose output (original behavior).

    Args:
        contract_path: Path to the contract file or directory (project root)
        debug: Enable debug output
        function_name: Optional function name to filter to (if None, shows all functions)
        contract_name: Optional contract name to filter to (if None, shows all contracts)
        embed: Enable IPython embed on errors for interactive debugging
        skip_compile: Skip compilation step (use existing artifacts)
        timeout_ms: Timeout in milliseconds for each optimization query
        skip_range_solving: If True, skip SMT optimization and use type bounds
        show_telemetry: If True, print solver telemetry at the end
    """
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger
    from slither.analyses.data_flow.smt_solver import Z3Solver
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

    # Enable telemetry if requested
    if show_telemetry:
        enable_telemetry()
        reset_telemetry()

    logger: DataFlowLogger = get_logger(enable_ipython_embed=embed, log_level="DEBUG")
    logger.info(LogMessages.ENGINE_START)

    logger.info("Loading contract from: {path}", path=contract_path)
    try:
        slither: Slither = Slither(contract_path, ignore_compile=skip_compile)
    except SlitherError as e:
        error_msg = str(e)
        # Check if this is a Foundry compilation error
        if "build-info" in error_msg or "Compilation failed" in error_msg:
            contract_path_obj = Path(contract_path)
            # Check if foundry.toml exists (indicates Foundry project)
            foundry_toml = contract_path_obj / "foundry.toml"
            if not foundry_toml.exists() and contract_path_obj.is_file():
                # If it's a file, check parent directory
                foundry_toml = contract_path_obj.parent / "foundry.toml"

            if foundry_toml.exists():
                logger.error(
                    "Foundry project compilation failed. Please build the project first:\n"
                    "  cd {project_dir}\n"
                    "  forge build",
                    project_dir=foundry_toml.parent,
                )
            else:
                logger.error(
                    "Compilation failed. Please ensure the project is built.\n"
                    "Original error: {error}",
                    error=error_msg,
                )
        else:
            logger.error("Slither initialization failed: {error}", error=error_msg)
        raise

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

    # Collect all contract names for error message
    all_contract_names = sorted(set(c.name for c in contracts))

    # Filter by contract name if specified
    if contract_name:
        contracts = [c for c in contracts if c.name == contract_name]
        if not contracts:
            console.print(f"[red]Contract '{contract_name}' not found![/red]")
            console.print(f"[dim]Available contracts: {', '.join(all_contract_names)}[/dim]")
            return
        logger.info("Filtered to contract: {contract_name}", contract_name=contract_name)

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

        # Create shared cache for all functions in this contract
        cache = RangeQueryCache(max_size=1000)

        for function in implemented_functions:
            try:
                solver = Z3Solver(use_optimizer=True)
                analysis: IntervalAnalysis = IntervalAnalysis(solver=solver)

                # Get the optimizer from the solver for reuse
                optimizer = solver.solver if hasattr(solver, "solver") else None

                analyze_function_verbose(
                    function,
                    analysis,
                    logger,
                    LogMessages,
                    debug=debug,
                    timeout_ms=timeout_ms,
                    skip_range_solving=skip_range_solving,
                    cache=cache,
                    optimizer=optimizer,
                )
            except Exception as e:
                # Log error with context, then stop execution
                logger.exception(
                    LogMessages.ERROR_ANALYSIS_FAILED,
                    error=str(e),
                    function_name=function.name,
                    embed_on_error=False,
                )
                raise

    logger.info(LogMessages.ENGINE_COMPLETE)

    # Print telemetry if enabled
    if show_telemetry:
        telemetry = get_telemetry()
        if telemetry:
            console.print("\n")
            telemetry.print_summary(console)


def show_test_output(
    contract_file: str, function_name: Optional[str] = None, contracts_dir: str = "../contracts/src"
) -> None:
    """Show verbose table output for a specific test contract/function.

    Args:
        contract_file: Name of the contract file (e.g., "FunctionArgs.sol") or full path
        function_name: Optional function name to filter to
        contracts_dir: Directory containing contract files (used if contract_file is just a filename)
    """
    # Check if contract_file is already a full path
    contract_file_path = Path(contract_file)
    if contract_file_path.is_absolute() or "/" in contract_file or "\\" in contract_file:
        # It's already a path, use it directly
        contract_path = contract_file_path.resolve()
    else:
        # It's just a filename, prepend contracts_dir
        contract_path = (Path(contracts_dir) / contract_file).resolve()

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
    from slither.analyses.data_flow.logger import get_logger, DataFlowLogger

    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="ERROR")

    run_verbose(str(contract_path), debug=False, function_name=function_name)
