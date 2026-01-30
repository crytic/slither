"""Verbose mode analysis functions for data flow analysis."""

from collections import defaultdict
from dataclasses import dataclass
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


# Default timeout for optimization queries
# 500ms is needed for correct results on 256-bit inequality constraints
DEFAULT_OPTIMIZE_TIMEOUT_MS = 500


@dataclass
class VerboseConfig:
    """Configuration for verbose analysis."""

    debug: bool = False
    timeout_ms: int = DEFAULT_OPTIMIZE_TIMEOUT_MS
    skip_range_solving: bool = False
    cache: Optional["RangeQueryCache"] = None
    show_telemetry: bool = False
    function_name: Optional[str] = None
    contract_name: Optional[str] = None
    embed: bool = False
    skip_compile: bool = False


def analyze_function_verbose(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
    config: Optional[VerboseConfig] = None,
) -> None:
    """Run interval analysis on a single function with verbose output."""
    if config is None:
        config = VerboseConfig()

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

    results = _run_engine_analysis(function, analysis, logger, LogMessages)
    line_data = _group_results_by_line(results, logger)

    solver = analysis.solver
    if not solver:
        logger.warning("No solver available for range solving")
        return

    _display_line_ranges(line_data, solver, logger, config)
    display_safety_violations(analysis.safety_violations)


def _run_engine_analysis(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
) -> Dict[Node, AnalysisState[IntervalAnalysis]]:
    """Run the engine analysis and return results."""
    logger.info(LogMessages.ENGINE_INIT, function_name=function.name)
    engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)

    logger.debug(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")
    engine.run_analysis()

    results = engine.result()
    logger.info("Analysis complete! Processed {count} nodes.", count=len(results))
    return results


def _group_results_by_line(
    results: Dict[Node, AnalysisState[IntervalAnalysis]],
    logger: "DataFlowLogger",
) -> Dict[int, Dict]:
    """Group analysis results by source line."""
    line_data: Dict[int, Dict] = defaultdict(
        lambda: {"code": None, "nodes": [], "variables": {}}
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

        post_state_vars = state.post.state.get_range_variables()
        if not post_state_vars:
            continue

        lines = _get_source_lines(node)
        node_code = _get_node_code(node)

        for line_num in lines:
            _add_node_to_line_data(
                line_data[line_num], node, node_code, post_state_vars, state
            )

    return line_data


def _get_source_lines(node: Node) -> List[int]:
    """Get source lines for a node."""
    if hasattr(node, "source_mapping") and node.source_mapping and node.source_mapping.lines:
        return node.source_mapping.lines
    return [-node.node_id]


def _get_node_code(node: Node) -> str:
    """Get display code for a node."""
    if node.expression:
        return str(node.expression)
    if hasattr(node, "source_mapping") and node.source_mapping:
        return node.source_mapping.content.strip()
    if str(node):
        return str(node)
    return ""


def _add_node_to_line_data(
    line_info: Dict,
    node: Node,
    node_code: str,
    post_state_vars: Dict[str, TrackedSMTVariable],
    state: AnalysisState[IntervalAnalysis],
) -> None:
    """Add a node's data to line info."""
    line_info["nodes"].append(node)

    if node_code and not line_info["code"]:
        line_info["code"] = node_code

    path_constraints = state.post.state.get_path_constraints()
    constraints_tuple = tuple(str(c) for c in path_constraints)
    used_vars = state.post.state.get_used_variables()

    for var_name, smt_var in post_state_vars.items():
        if _should_skip_variable(var_name, used_vars):
            continue

        var_key = (var_name, constraints_tuple)
        if var_key not in line_info["variables"]:
            line_info["variables"][var_key] = (smt_var, path_constraints, state)


def _should_skip_variable(var_name: str, used_vars: set) -> bool:
    """Check if variable should be skipped from display."""
    if var_name.startswith("CONST_") or var_name.startswith("TMP_"):
        return True
    if var_name not in used_vars:
        return True
    if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
        return True
    return False


def _display_line_ranges(
    line_data: Dict[int, Dict],
    solver,
    logger: "DataFlowLogger",
    config: VerboseConfig,
) -> None:
    """Display ranges for each line."""

    for line_num in sorted(line_data.keys()):
        line_info = line_data[line_num]
        if not line_info["variables"]:
            continue

        if line_info["code"]:
            console.print(f"\n[bold white]Code:[/bold white] [dim]{line_info['code']}[/dim]")

        variable_results = _compute_variable_ranges(
            line_info["variables"], solver, logger, config
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


def _compute_variable_ranges(
    variables: Dict,
    solver,
    logger: "DataFlowLogger",
    config: VerboseConfig,
) -> List[Dict]:
    """Compute ranges for variables at a line."""
    from slither.analyses.data_flow.analysis import solve_variable_range, RangeQueryConfig

    results: List[Dict] = []
    for (var_name, _), (smt_var, path_constraints, _) in sorted(
        variables.items(), key=lambda x: x[0][0]
    ):
        if config.debug:
            console.print(f"\n[bold]Solving range for: {var_name}[/bold]")

        range_config = RangeQueryConfig(
            path_constraints=path_constraints,
            debug=config.debug,
            timeout_ms=config.timeout_ms,
            skip_optimization=config.skip_range_solving,
            cache=config.cache,
        )
        min_result, max_result = solve_variable_range(solver, smt_var, range_config)

        if min_result and max_result:
            results.append({
                "name": var_name,
                "sort": smt_var.sort,
                "min": min_result,
                "max": max_result,
            })
        else:
            logger.debug("Could not solve range for variable {var_name}", var_name=var_name)

    return results


def run_verbose(
    contract_path: str,
    config: Optional[VerboseConfig] = None,
) -> None:
    """Run analysis with verbose output.

    Args:
        contract_path: Path to the contract file or directory.
        config: Optional configuration for verbose analysis. If None, uses defaults.
    """
    from slither.analyses.data_flow.logger import get_logger, LogMessages

    if config is None:
        config = VerboseConfig()

    if config.show_telemetry:
        enable_telemetry()
        reset_telemetry()

    logger = get_logger(enable_ipython_embed=config.embed, log_level="DEBUG")
    logger.info(LogMessages.ENGINE_START)

    contracts = _load_contracts(contract_path, config.skip_compile, logger)
    if contracts is None:
        return

    contracts = _filter_contracts(contracts, config.contract_name, logger)
    if contracts is None:
        return

    logger.info("Found {count} contract(s)", count=len(contracts))
    logger.info(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")

    for contract in contracts:
        _process_contract_verbose(contract, logger, LogMessages, config)

    logger.info(LogMessages.ENGINE_COMPLETE)
    _print_telemetry_if_enabled(config.show_telemetry)


def _load_contracts(
    contract_path: str, skip_compile: bool, logger: "DataFlowLogger"
) -> Optional[List[Contract]]:
    """Load contracts from path."""
    logger.info("Loading contract from: {path}", path=contract_path)
    try:
        slither: Slither = Slither(contract_path, ignore_compile=skip_compile)
    except SlitherError as e:
        _handle_slither_error(e, contract_path, logger)
        raise

    contracts: List[Contract] = []
    if slither.compilation_units:
        for cu in slither.compilation_units:
            contracts.extend(cu.contracts)
    else:
        contracts = slither.contracts

    if not contracts:
        logger.warning("No contracts found!")
        return None

    return contracts


def _handle_slither_error(e: SlitherError, contract_path: str, logger: "DataFlowLogger") -> None:
    """Handle Slither initialization error."""
    error_msg = str(e)
    if "build-info" not in error_msg and "Compilation failed" not in error_msg:
        logger.error("Slither initialization failed: {error}", error=error_msg)
        return

    contract_path_obj = Path(contract_path)
    foundry_toml = contract_path_obj / "foundry.toml"
    if not foundry_toml.exists() and contract_path_obj.is_file():
        foundry_toml = contract_path_obj.parent / "foundry.toml"

    if foundry_toml.exists():
        logger.error(
            "Foundry project compilation failed. Please build the project first:\n"
            "  cd {project_dir}\n  forge build",
            project_dir=foundry_toml.parent,
        )
    else:
        logger.error(
            "Compilation failed. Please ensure the project is built.\nOriginal error: {error}",
            error=error_msg,
        )


def _filter_contracts(
    contracts: List[Contract], contract_name: Optional[str], logger: "DataFlowLogger"
) -> Optional[List[Contract]]:
    """Filter contracts by name if specified."""
    if not contract_name:
        return contracts

    all_contract_names = sorted(set(c.name for c in contracts))
    filtered = [c for c in contracts if c.name == contract_name]

    if not filtered:
        console.print(f"[red]Contract '{contract_name}' not found![/red]")
        console.print(f"[dim]Available contracts: {', '.join(all_contract_names)}[/dim]")
        return None

    logger.info("Filtered to contract: {contract_name}", contract_name=contract_name)
    return filtered


def _process_contract_verbose(
    contract: Contract,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
    config: VerboseConfig,
) -> None:
    """Process a single contract in verbose mode."""
    from slither.analyses.data_flow.smt_solver import Z3Solver
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

    logger.info("Processing contract: {contract_name}", contract_name=contract.name)

    functions = _get_implemented_functions(contract, config.function_name, logger)
    if not functions:
        return

    logger.info(
        "Found {count} implemented function(s) in {contract_name}",
        count=len(functions),
        contract_name=contract.name,
    )

    cache = RangeQueryCache(max_size=1000)
    func_config = VerboseConfig(
        debug=config.debug,
        timeout_ms=config.timeout_ms,
        skip_range_solving=config.skip_range_solving,
        cache=cache,
    )
    for function in functions:
        try:
            solver = Z3Solver(use_optimizer=True)
            analysis = IntervalAnalysis(solver=solver)
            analyze_function_verbose(function, analysis, logger, LogMessages, func_config)
        except Exception as e:
            logger.exception(
                LogMessages.ERROR_ANALYSIS_FAILED, error=str(e),
                function_name=function.name, embed_on_error=False,
            )
            raise


def _get_implemented_functions(
    contract: Contract, function_name: Optional[str], logger: "DataFlowLogger"
) -> List[Function]:
    """Get implemented functions, optionally filtered by name."""
    functions = contract.functions_and_modifiers_declared
    implemented = [f for f in functions if f.is_implemented and not f.is_constructor]

    if function_name:
        implemented = [f for f in implemented if f.name == function_name]
        if not implemented:
            msg = f"[yellow]Function '{function_name}' not found in '{contract.name}'[/yellow]"
            console.print(msg)
            return []

    if not implemented:
        logger.warning(
            "No implemented functions found in {contract_name}", contract_name=contract.name
        )

    return implemented


def _print_telemetry_if_enabled(show_telemetry: bool) -> None:
    """Print telemetry summary if enabled."""
    if not show_telemetry:
        return
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
        contracts_dir: Directory containing contract files (for relative paths)
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
    from slither.analyses.data_flow.logger import get_logger

    get_logger(enable_ipython_embed=False, log_level="ERROR")

    config = VerboseConfig(debug=False, function_name=function_name)
    run_verbose(str(contract_path), config)
