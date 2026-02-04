"""Main entry point for data flow analysis with annotated source output.

This module provides a clean CLI for running interval analysis and displaying
results as annotated source code with tree-style variable range annotations.
Supports both human-readable annotated source and JSON output for testing.
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from slither import Slither
from slither.analyses.data_flow.analysis_models import (
    AnnotatedFunction,
    AnnotatedLine,
    FunctionBounds,
    LineAnnotation,
)
from slither.analyses.data_flow.source_view import (
    build_annotation_from_range,
    console,
    render_annotated_function,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.core.cfg.node import Node
    from slither.core.declarations.contract import Contract
    from slither.core.declarations.function import Function

# Default timeout for optimization queries (milliseconds)
# Importing from analysis.py to keep timeout consistent
from slither.analyses.data_flow.analysis import DEFAULT_OPTIMIZE_TIMEOUT_MS as DEFAULT_TIMEOUT_MS


@dataclass
class AnalysisConfig:
    """Configuration for the analysis run."""

    contract_name: str | None = None
    function_name: str | None = None
    show_bounds: bool = False
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    skip_solving: bool = False
    show_telemetry: bool = False
    skip_compile: bool = False
    exact_values: bool = False
    show_all: bool = False
    show_ssa: bool = False
    json_output: bool = False


def main() -> int:
    """Main entry point for the CLI."""
    parser = _create_parser()
    args = parser.parse_args()

    config = AnalysisConfig(
        contract_name=args.contract_name,
        function_name=args.function,
        show_bounds=args.bounds,
        timeout_ms=args.timeout,
        skip_solving=args.skip_solving,
        show_telemetry=args.telemetry,
        skip_compile=args.skip_compile,
        exact_values=args.exact,
        show_all=args.all,
        show_ssa=args.ssa,
        json_output=args.json,
    )

    return analyze_contract(args.path, config)


def _create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Slither Data Flow Analysis - Annotated Source View",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path", type=str, help="Path to contract file or project directory"
    )
    parser.add_argument(
        "-c",
        "--contract-name",
        type=str,
        metavar="NAME",
        help="Filter to specific contract",
    )
    parser.add_argument(
        "-f", "--function", type=str, metavar="NAME", help="Filter to specific function"
    )
    parser.add_argument(
        "--bounds", action="store_true", help="Show bounds/constraints header"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        metavar="MS",
        help=f"SMT solver timeout in ms (default: {DEFAULT_TIMEOUT_MS})",
    )
    parser.add_argument(
        "--skip-solving",
        action="store_true",
        help="Skip SMT optimization and use conservative type bounds",
    )
    parser.add_argument(
        "--telemetry", action="store_true", help="Show solver statistics"
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip compilation (use existing build artifacts)",
    )
    parser.add_argument(
        "--exact",
        action="store_true",
        help="Show exact decimal values instead of exponential form",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all variables including temporaries (TMP_, CONST_, REF_)",
    )
    parser.add_argument(
        "--ssa",
        action="store_true",
        help="Show full SSA variable names (with |suffix)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format (for testing/programmatic use)",
    )
    return parser


def analyze_contract(path: str, config: AnalysisConfig) -> int:
    """Load and analyze a contract, displaying annotated source or JSON."""
    from slither.analyses.data_flow.smt_solver import Z3Solver
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache
    from slither.analyses.data_flow.smt_solver.telemetry import (
        enable_telemetry,
        get_telemetry,
        reset_telemetry,
    )

    if config.show_telemetry:
        enable_telemetry()
        reset_telemetry()

    try:
        slither = Slither(path, ignore_compile=config.skip_compile)
    except Exception as e:
        console.print(f"[red]Failed to load contract: {e}[/red]")
        return 1

    contracts = _get_contracts(slither)
    if config.contract_name:
        contracts = [c for c in contracts if c.name == config.contract_name]
        if not contracts:
            console.print(f"[red]Contract '{config.contract_name}' not found[/red]")
            return 1

    cache = RangeQueryCache(max_size=1000)

    # JSON output mode - collect results for all contracts
    if config.json_output:
        json_output = _analyze_contracts_json(contracts, config, cache)
        print(json.dumps(json_output, indent=2, sort_keys=True))
        return 0

    # Annotated source output mode
    for contract in contracts:
        functions = _get_functions(contract, config.function_name)
        if not functions:
            continue

        for function in functions:
            solver = Z3Solver(use_optimizer=True)
            annotated = analyze_function(function, solver, config, cache)
            if annotated:
                render_annotated_function(annotated)
                console.print()

    if config.show_telemetry:
        telemetry = get_telemetry()
        if telemetry:
            console.print()
            telemetry.print_summary(console)

    return 0


def _get_contracts(slither: Slither) -> list["Contract"]:
    """Extract contracts from Slither instance."""
    contracts = []
    if slither.compilation_units:
        for cu in slither.compilation_units:
            contracts.extend(cu.contracts)
    else:
        contracts = list(slither.contracts)
    return contracts


def _get_functions(contract: "Contract", function_name: str | None) -> list["Function"]:
    """Get implemented functions from a contract, optionally filtered."""
    functions = contract.functions_and_modifiers_declared
    implemented = [f for f in functions if f.is_implemented and not f.is_constructor]
    if function_name:
        implemented = [f for f in implemented if f.name == function_name]
    return implemented


def _analyze_contracts_json(
    contracts: list["Contract"],
    config: AnalysisConfig,
    cache: "RangeQueryCache",
) -> dict:
    """Analyze contracts and return JSON-serializable results."""
    from slither.analyses.data_flow.smt_solver import Z3Solver

    output: dict = {}

    for contract in contracts:
        contract_data: dict = {}
        functions = _get_functions(contract, config.function_name)

        for function in functions:
            solver = Z3Solver(use_optimizer=True)
            func_result = _analyze_function_json(function, solver, config, cache)
            if func_result:
                contract_data[function.name] = func_result

        if contract_data:
            output[contract.name] = contract_data

    return output


def _analyze_function_json(
    function: "Function",
    solver: "SMTSolver",
    config: AnalysisConfig,
    cache: "RangeQueryCache",
) -> dict | None:
    """Analyze a function and return JSON-serializable result."""
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import (
        IntervalAnalysis,
    )
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        DomainVariant,
    )
    from slither.analyses.data_flow.analysis import RangeQueryConfig, solve_variable_range
    from slither.analyses.data_flow.engine.engine import Engine

    if not function.nodes:
        return None

    analysis = IntervalAnalysis(solver=solver, timeout_ms=config.timeout_ms)
    engine = Engine.new(analysis=analysis, function=function)
    engine.run_analysis()
    results = engine.result()

    # Find nodes to collect results from (exit nodes)
    nodes_to_process = _get_exit_nodes(function, results)

    variables: dict = {}

    for node in nodes_to_process:
        if node not in results:
            continue
        state = results[node]
        if state.post.variant != DomainVariant.STATE:
            continue

        post_state = state.post.state
        range_vars = post_state.get_range_variables()
        path_constraints = post_state.get_path_constraints()

        for var_name, smt_var in range_vars.items():
            if _should_skip_var_json(var_name, variables):
                continue

            range_config = RangeQueryConfig(
                path_constraints=path_constraints,
                timeout_ms=config.timeout_ms,
                skip_optimization=config.skip_solving,
                cache=cache,
            )
            min_result, max_result = solve_variable_range(solver, smt_var, range_config)

            if not min_result or not max_result:
                continue

            # Handle unreachable paths
            if min_result.get("unreachable"):
                variables[var_name] = {
                    "range": "⊥ (unreachable)",
                    "overflow": "NO",
                }
                continue

            min_val = min_result["value"]
            max_val = max_result["value"]
            has_overflow = min_result.get("overflow", False) or max_result.get(
                "overflow", False
            )

            # Handle wrapped ranges
            if min_val > max_val:
                range_str = f"[{max_val}, {min_val}]"
            else:
                range_str = f"[{min_val}, {max_val}]"

            variables[var_name] = {
                "range": range_str,
                "overflow": "YES" if has_overflow else "NO",
            }

    if not variables:
        return None

    return {"variables": variables}


def _get_exit_nodes(function: "Function", results: dict) -> list["Node"]:
    """Get exit nodes for result collection."""
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        DomainVariant,
    )

    return_nodes = [node for node in function.nodes if not node.sons]
    if not return_nodes and function.nodes:
        return_nodes = [function.nodes[-1]]

    # Check if all return nodes are unreachable
    all_unreachable = all(
        node not in results or results[node].post.variant != DomainVariant.STATE
        for node in return_nodes
    )

    if all_unreachable:
        for node in reversed(function.nodes):
            if node in results and results[node].post.variant == DomainVariant.STATE:
                return [node]

    return return_nodes


def _should_skip_var_json(
    var_name: str,
    existing: dict,
) -> bool:
    """Check if variable should be skipped for JSON output.

    JSON output includes everything except:
    - Duplicates
    - Internal call variables (prefixed with _lib or _int)
    """
    if var_name in existing:
        return True
    if var_name.startswith("_lib") or var_name.startswith("_int"):
        return True
    return False


def analyze_function(
    function: "Function",
    solver: "SMTSolver",
    config: AnalysisConfig,
    cache: "RangeQueryCache",
) -> AnnotatedFunction | None:
    """Run analysis on a single function and build annotated view."""
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import (
        IntervalAnalysis,
    )
    from slither.analyses.data_flow.engine.engine import Engine

    analysis = IntervalAnalysis(solver=solver, timeout_ms=config.timeout_ms)
    if not function.nodes:
        return None

    engine = Engine.new(analysis=analysis, function=function)
    engine.run_analysis()
    results = engine.result()

    return build_annotated_function(function, results, solver, config, cache)


def build_annotated_function(
    function: "Function",
    results: dict["Node", "object"],
    solver: "SMTSolver",
    config: AnalysisConfig,
    cache: "RangeQueryCache",
) -> AnnotatedFunction | None:
    """Map analysis results to annotated source view."""
    source_lines = _read_source_lines(function)
    if not source_lines:
        return None

    start_line, end_line = _get_function_line_range(function)
    lines: dict[int, AnnotatedLine] = {}

    # Initialize all lines from source
    for line_num, text in source_lines.items():
        lines[line_num] = AnnotatedLine(
            line_number=line_num,
            source_text=text,
            is_entry=(line_num == start_line),
            is_exit=(line_num == end_line),
        )

    # Collect annotations from analysis results
    line_annotations = _collect_line_annotations(results, solver, config, cache)

    # Merge annotations into lines
    for line_num, annotations in line_annotations.items():
        if line_num in lines:
            lines[line_num].annotations.extend(annotations)

    bounds = None
    if config.show_bounds:
        bounds = _build_function_bounds(function, results)

    filename = _get_function_filename(function)

    return AnnotatedFunction(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
        filename=filename,
        start_line=start_line,
        end_line=end_line,
        lines=lines,
        bounds=bounds,
    )


def _read_source_lines(function: "Function") -> dict[int, str]:
    """Read source code lines for a function."""
    if not hasattr(function, "source_mapping") or not function.source_mapping:
        return {}

    sm = function.source_mapping
    if not sm.filename or not sm.lines:
        return {}

    # Get source code from Slither
    try:
        filename = str(sm.filename.absolute)
        slither = function.contract.compilation_unit.core if function.contract else None
        if not slither:
            return {}

        source_code = slither.source_code.get(filename)
        if not source_code:
            return {}

        all_lines = source_code.splitlines()
        start_line = min(sm.lines)
        end_line = max(sm.lines)

        result = {}
        for line_num in range(start_line, end_line + 1):
            if 0 < line_num <= len(all_lines):
                result[line_num] = all_lines[line_num - 1]

        return result
    except Exception:
        return {}


def _get_function_line_range(function: "Function") -> tuple[int, int]:
    """Get the start and end line numbers for a function."""
    if hasattr(function, "source_mapping") and function.source_mapping:
        lines = function.source_mapping.lines
        if lines:
            return min(lines), max(lines)
    return 1, 1


def _get_function_filename(function: "Function") -> str:
    """Get the filename for a function."""
    if hasattr(function, "source_mapping") and function.source_mapping:
        if function.source_mapping.filename:
            return str(function.source_mapping.filename.short)
    return "unknown"


def _collect_line_annotations(
    results: dict["Node", "object"],
    solver: "SMTSolver",
    config: AnalysisConfig,
    cache: "RangeQueryCache",
) -> dict[int, list[LineAnnotation]]:
    """Collect variable annotations grouped by source line."""
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        DomainVariant,
    )

    line_annotations: dict[int, list[LineAnnotation]] = defaultdict(list)
    seen_vars: set[tuple[int, str]] = set()

    for node, state in results.items():
        if state.post.variant != DomainVariant.STATE:
            continue

        post_state = state.post.state
        range_vars = post_state.get_range_variables()
        used_vars = post_state.get_used_variables()
        path_constraints = post_state.get_path_constraints()

        lines = _get_node_lines(node)
        if not lines:
            continue

        primary_line = lines[0]

        # Build TMP expression mapping from node IRs
        tmp_expressions = _build_tmp_expressions(node)

        for var_name, smt_var in range_vars.items():
            if _should_skip_variable(var_name, used_vars, config.show_all):
                continue

            var_key = (primary_line, var_name)
            if var_key in seen_vars:
                continue
            seen_vars.add(var_key)

            annotation = _create_annotation(
                var_name,
                smt_var,
                path_constraints,
                solver,
                config,
                cache,
                tmp_expressions,
            )
            if annotation:
                line_annotations[primary_line].append(annotation)

    return line_annotations


def _get_node_lines(node: "Node") -> list[int]:
    """Get source lines for a CFG node."""
    if hasattr(node, "source_mapping") and node.source_mapping:
        if node.source_mapping.lines:
            return list(node.source_mapping.lines)
    return []


def _should_skip_variable(
    var_name: str, used_vars: set[str], show_all: bool = False
) -> bool:
    """Check if variable should be skipped from annotations."""
    # Always skip internal call variables (library and internal functions)
    if var_name.startswith("_lib") or var_name.startswith("_int"):
        return True

    # In show_all mode, only skip unused variables
    if show_all:
        return var_name not in used_vars

    if var_name.startswith("CONST_") or var_name.startswith("TMP_"):
        return True
    if var_name.startswith("REF_"):
        return True
    if var_name not in used_vars:
        return True
    if any(var_name.startswith(prefix) for prefix in ("block.", "msg.", "tx.")):
        return True
    return False


def _binary_op_symbol(op_name: str) -> str:
    """Convert binary operation name to symbol."""
    symbols = {
        "addition": "+",
        "subtraction": "-",
        "multiplication": "*",
        "division": "/",
        "modulo": "%",
        "power": "**",
        "less": "<",
        "greater": ">",
        "less_equal": "<=",
        "greater_equal": ">=",
        "equal": "==",
        "not_equal": "!=",
        "and": "&&",
        "or": "||",
        "left_shift": "<<",
        "right_shift": ">>",
    }
    return symbols.get(op_name.lower(), op_name)


def _build_tmp_expressions(node: "Node") -> dict[str, str]:
    """Build a mapping of TMP variable names to their expressions."""
    tmp_expr: dict[str, str] = {}
    if not hasattr(node, "irs"):
        return tmp_expr

    for ir in node.irs:
        if not hasattr(ir, "lvalue") or ir.lvalue is None:
            continue

        lvalue_name = str(ir.lvalue)
        if not lvalue_name.startswith("TMP_"):
            continue

        ir_type = type(ir).__name__

        if ir_type == "TypeConversion":
            # CONVERT x to type
            var = getattr(ir, "variable", None)
            target_type = getattr(ir, "type", None)
            if var and target_type:
                tmp_expr[lvalue_name] = f"{target_type}({var})"
        elif ir_type == "Binary":
            # x op y
            left = getattr(ir, "variable_left", None)
            right = getattr(ir, "variable_right", None)
            op = getattr(ir, "type", None)
            if left and right and op:
                op_str = _binary_op_symbol(str(op).split(".")[-1])
                tmp_expr[lvalue_name] = f"{left} {op_str} {right}"

    return tmp_expr


def _create_annotation(
    var_name: str,
    smt_var: "TrackedSMTVariable",
    path_constraints: list,
    solver: "SMTSolver",
    config: AnalysisConfig,
    cache: "RangeQueryCache",
    tmp_expressions: dict[str, str] | None = None,
) -> LineAnnotation | None:
    """Create a LineAnnotation from analysis data."""
    from slither.analyses.data_flow.analysis import (
        RangeQueryConfig,
        solve_variable_range,
    )

    range_config = RangeQueryConfig(
        path_constraints=path_constraints,
        timeout_ms=config.timeout_ms,
        skip_optimization=config.skip_solving,
        cache=cache,
    )
    min_result, max_result = solve_variable_range(solver, smt_var, range_config)

    if not min_result or not max_result:
        return None

    # Check for unreachable path
    if min_result.get("unreachable"):
        display_name = _simplify_var_name(var_name, keep_ssa=config.show_ssa)
        if var_name.startswith("TMP_") and tmp_expressions:
            expr = tmp_expressions.get(var_name)
            if expr:
                display_name = f"{display_name} = {expr}"
        return LineAnnotation(
            variable_name=display_name,
            range_min="⊥",
            range_max="⊥",
            constraints="(unreachable)",
        )

    min_val = min_result["value"]
    max_val = max_result["value"]

    bit_width = _get_bit_width(smt_var)
    is_signed = _is_signed(smt_var)

    # Detect special constraints
    constraints = _detect_constraints(min_val, max_val)

    # Only mark actual return statements as returns (not TMP variables)
    is_return = "return" in var_name.lower() and not var_name.startswith("TMP_")

    # Simplify variable name for display (keep SSA suffix if requested)
    display_name = _simplify_var_name(var_name, keep_ssa=config.show_ssa)

    # For TMP variables, add the expression they represent
    if var_name.startswith("TMP_") and tmp_expressions:
        expr = tmp_expressions.get(var_name)
        if expr:
            display_name = f"{display_name} = {expr}"

    # All annotations at same indent (column=0)
    column = 0

    return build_annotation_from_range(
        var_name=display_name,
        min_val=min_val,
        max_val=max_val,
        bit_width=bit_width,
        is_signed=is_signed,
        column=column,
        is_return=is_return,
        extra_constraints=constraints,
        exact=config.exact_values,
    )


def _simplify_var_name(var_name: str, keep_ssa: bool = False) -> str:
    """Simplify a verbose variable name for display.

    Args:
        var_name: The full variable name.
        keep_ssa: If True, preserve the SSA suffix (e.g., |a_1).
    """
    # Extract SSA suffix if present
    ssa_suffix = ""
    if "|" in var_name:
        base_name, ssa_suffix = var_name.rsplit("|", 1)
    else:
        base_name = var_name

    # Handle indexed array access like Contract.balances[Contract.func().dst]
    if "[" in base_name and "]" in base_name:
        bracket_start = base_name.index("[")
        bracket_end = base_name.rindex("]")
        array_part = base_name[:bracket_start]
        index_part = base_name[bracket_start + 1 : bracket_end]

        # Simplify the array name
        if "." in array_part:
            array_part = array_part.rsplit(".", 1)[1]

        # Simplify the index (recursively)
        index_part = _simplify_var_name(index_part, keep_ssa)

        result = f"{array_part}[{index_part}]"
        return f"{result}|{ssa_suffix}" if keep_ssa and ssa_suffix else result

    # Extract just the variable part from Contract.function().var patterns
    if "()." in base_name:
        base_name = base_name.split("().", 1)[1]
    elif "." in base_name:
        # Handle Contract.var or Contract.function.var patterns
        # But preserve struct field access like "user_2.id"
        parts = base_name.split(".")
        if len(parts) >= 2:
            # Check if first part looks like an SSA variable (ends with _N)
            first_part = parts[0]
            is_struct_field = (
                "_" in first_part
                and first_part.rsplit("_", 1)[-1].isdigit()
            )
            if not is_struct_field:
                base_name = parts[-1]

    return f"{base_name}|{ssa_suffix}" if keep_ssa and ssa_suffix else base_name


def _get_bit_width(smt_var: "TrackedSMTVariable") -> int:
    """Extract bit width from SMT variable."""
    metadata = smt_var.base.metadata
    bit_width = metadata.get("bit_width")
    if bit_width is None and smt_var.sort.parameters:
        bit_width = smt_var.sort.parameters[0]
    return int(bit_width) if bit_width else 256


def _is_signed(smt_var: "TrackedSMTVariable") -> bool:
    """Check if SMT variable is signed."""
    return bool(smt_var.base.metadata.get("is_signed", False))


def _detect_constraints(min_val: int, max_val: int) -> str:
    """Detect special constraints worth noting.

    The range [min, max] already shows bounds, so we only add constraints
    that provide additional insight beyond what the range shows.
    Currently returns empty - the range itself is sufficient information.
    """
    # The range already shows whether zero is possible (min > 0 means not zero)
    # No need to redundantly add "&& != 0" since the range is explicit
    del min_val, max_val  # Unused, kept for potential future enhancements
    return ""


def _build_function_bounds(
    function: "Function", results: dict["Node", "object"]
) -> FunctionBounds | None:
    """Build the bounds/constraints header for a function."""
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        DomainVariant,
    )

    constraints: list[str] = []

    # Collect path constraints from entry node
    entry = function.entry_point
    if entry and entry in results:
        state = results[entry]
        if state.post.variant == DomainVariant.STATE:
            path_constraints = state.post.state.get_path_constraints()
            for constraint in path_constraints:
                constraints.append(f"({constraint}) == true")

    if not constraints:
        return None

    signature = _build_signature(function)
    return FunctionBounds(signature=signature, constraints=constraints)


def _build_signature(function: "Function") -> str:
    """Build a function signature string."""
    params = []
    for param in function.parameters:
        param_type = str(param.type) if param.type else "unknown"
        params.append(f"{param_type}")
    param_str = ", ".join(params)
    return f"{function.name}({param_str})"


if __name__ == "__main__":
    sys.exit(main())
