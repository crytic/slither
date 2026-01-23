"""Visualization tool for rounding direction analysis."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich import box
from rich.console import Console
from rich.table import Table

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import RoundingAnalysis
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.utils.utils import RVALUE

console = Console()


@dataclass
class VariableTagInfo:
    name: str
    tag: RoundingTag
    operation: Optional[str] = None


@dataclass
class NodeAnalysis:
    node_id: int
    node_type: str
    expression: Optional[str] = None
    variables: Dict[str, VariableTagInfo] = field(default_factory=dict)


@dataclass
class FunctionAnalysis:
    function_name: str
    contract_name: str
    nodes: List[NodeAnalysis] = field(default_factory=list)
    return_tags: Dict[str, RoundingTag] = field(default_factory=dict)
    expected_tag: Optional[RoundingTag] = None
    inconsistencies: List[str] = field(default_factory=list)


def format_tag(tag: RoundingTag) -> str:
    """Format rounding tag with emoji and color."""
    formats = {
        RoundingTag.UP: ("🔼 UP", "green"),
        RoundingTag.DOWN: ("🔽 DOWN", "red"),
        RoundingTag.NEUTRAL: ("⚪ NEUTRAL", "white"),
        RoundingTag.UNKNOWN: ("❓ UNKNOWN", "yellow"),
    }
    text, color = formats.get(tag, (str(tag), "white"))
    return f"[{color}]{text}[/{color}]"


def get_var_name(var: Optional[Union[RVALUE, Variable]]) -> str:
    """Get variable name, or string representation if not a Variable."""
    if isinstance(var, Variable):
        return var.name
    return str(var) if var else "?"


def get_tag(domain: RoundingDomain, var: Optional[Union[RVALUE, Variable]]) -> RoundingTag:
    """Get rounding tag for a variable, defaulting to NEUTRAL for non-variables."""
    if isinstance(var, Variable):
        return domain.state.get_tag(var)
    return RoundingTag.NEUTRAL


def get_unknown_reason(domain: RoundingDomain, var: Variable, tag: RoundingTag) -> Optional[str]:
    """Get unknown reason if tag is UNKNOWN."""
    if tag == RoundingTag.UNKNOWN:
        return domain.state.get_unknown_reason(var)
    return None


def extract_binary_info(
    domain: RoundingDomain, operation: Binary
) -> tuple[str, RoundingTag, str, RoundingTag, str, RoundingTag]:
    """Extract names and tags for binary operation operands and result."""
    left_name = get_var_name(operation.variable_left)
    right_name = get_var_name(operation.variable_right)
    result_name = get_var_name(operation.lvalue)
    left_tag = get_tag(domain, operation.variable_left)
    right_tag = get_tag(domain, operation.variable_right)
    result_tag = get_tag(domain, operation.lvalue)
    return left_name, left_tag, right_name, right_tag, result_name, result_tag


def extract_assignment_info(
    domain: RoundingDomain, operation: Assignment
) -> tuple[str, RoundingTag, str, RoundingTag]:
    """Extract names and tags for assignment rvalue and lvalue."""
    rvalue_name = get_var_name(operation.rvalue)
    lvalue_name = get_var_name(operation.lvalue)
    rvalue_tag = get_tag(domain, operation.rvalue)
    lvalue_tag = get_tag(domain, operation.lvalue)
    return rvalue_name, rvalue_tag, lvalue_name, lvalue_tag


def get_function_name(operation: Union[InternalCall, HighLevelCall, LibraryCall]) -> str:
    """Extract function name from call operation."""
    if isinstance(operation, InternalCall):
        return operation.function.name if operation.function else str(operation.function_name)
    return str(operation.function_name.value)


def build_operation_str(
    result_name: str,
    result_tag: RoundingTag,
    op_str: str,
    left_name: str = "",
    left_tag: RoundingTag = RoundingTag.NEUTRAL,
    right_name: str = "",
    right_tag: RoundingTag = RoundingTag.NEUTRAL,
    unknown_reason: Optional[str] = None,
    extra_note: str = "",
) -> str:
    """Build operation string with tag information."""
    if left_name and right_name:
        tags_str = f"[{left_name}:{left_tag.name}, {right_name}:{right_tag.name} -> {result_name}:{result_tag.name}]"
    else:
        tags_str = f"[-> {result_name}:{result_tag.name}]"

    result = f"{op_str} {tags_str}"
    if extra_note:
        result += f" ({extra_note})"
    if unknown_reason:
        result += f" (UNKNOWN: {unknown_reason})"
    return result


def analyze_function(function: FunctionContract) -> FunctionAnalysis:
    """Analyze a function and extract all variable rounding tags."""
    func_analysis = FunctionAnalysis(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
    )

    # Infer expected rounding from function name
    function_name_lower = function.name.lower()
    if "down" in function_name_lower or "floor" in function_name_lower:
        func_analysis.expected_tag = RoundingTag.DOWN
    elif "up" in function_name_lower or "ceil" in function_name_lower:
        func_analysis.expected_tag = RoundingTag.UP

    # Run analysis
    rounding_analysis = RoundingAnalysis()
    engine = Engine.new(rounding_analysis, function)
    engine.run_analysis()
    node_results: Dict[Node, AnalysisState] = engine.result()
    func_analysis.inconsistencies = rounding_analysis.inconsistencies

    # Process each node
    for node in function.nodes:
        if node not in node_results or node_results[node].post.variant != DomainVariant.STATE:
            continue

        domain = node_results[node].post
        node_analysis = NodeAnalysis(
            node_id=node.node_id,
            node_type=node.type.name,
            expression=str(node.expression) if node.expression else None,
        )

        if not node.irs_ssa:
            func_analysis.nodes.append(node_analysis)
            continue

        for operation in node.irs_ssa:
            if isinstance(operation, Binary) and operation.lvalue:
                left_name, left_tag, right_name, right_tag, result_name, result_tag = (
                    extract_binary_info(domain, operation)
                )
                unknown_reason = (
                    get_unknown_reason(domain, operation.lvalue, result_tag)
                    if isinstance(operation.lvalue, Variable)
                    else None
                )

                operator_symbol = {
                    BinaryType.ADDITION: "+",
                    BinaryType.SUBTRACTION: "-",
                    BinaryType.MULTIPLICATION: "*",
                    BinaryType.DIVISION: "/",
                }.get(operation.type, str(operation.type.value))
                operation_string = f"{result_name} = {left_name} {operator_symbol} {right_name}"

                annotation = ""
                if operation.type == BinaryType.DIVISION:
                    annotation = (
                        "inferred from ceiling division pattern as UP"
                        if result_tag == RoundingTag.UP
                        else "inferred from denominator inversion"
                    )

                operation_str = build_operation_str(
                    result_name,
                    result_tag,
                    operation_string,
                    left_name,
                    left_tag,
                    right_name,
                    right_tag,
                    unknown_reason,
                    annotation,
                )
                node_analysis.variables[result_name] = VariableTagInfo(
                    result_name, result_tag, operation_str
                )

            elif isinstance(operation, Assignment) and operation.lvalue:
                rvalue_name, rvalue_tag, lvalue_name, lvalue_tag = extract_assignment_info(
                    domain, operation
                )
                unknown_reason = (
                    get_unknown_reason(domain, operation.lvalue, lvalue_tag)
                    if isinstance(operation.lvalue, Variable)
                    else None
                )

                operation_string = f"{lvalue_name} = {rvalue_name}"
                operation_str = build_operation_str(
                    lvalue_name,
                    lvalue_tag,
                    operation_string,
                    rvalue_name,
                    rvalue_tag,
                    unknown_reason=unknown_reason,
                )
                node_analysis.variables[lvalue_name] = VariableTagInfo(
                    lvalue_name, lvalue_tag, operation_str
                )

            elif (
                isinstance(operation, (InternalCall, HighLevelCall, LibraryCall))
                and operation.lvalue
            ):
                result_name = get_var_name(operation.lvalue)
                result_tag = get_tag(domain, operation.lvalue)
                unknown_reason = (
                    get_unknown_reason(domain, operation.lvalue, result_tag)
                    if isinstance(operation.lvalue, Variable)
                    else None
                )
                called_function_name = get_function_name(operation)

                argument_tags = [
                    f"{get_var_name(arg)}:{get_tag(domain, arg).name}"
                    for arg in operation.arguments
                ]
                arguments_summary = ", ".join(argument_tags) if argument_tags else "no-args"
                operation_string = f"{result_name} = {called_function_name}(...)"
                operation_str = build_operation_str(
                    result_name, result_tag, operation_string, unknown_reason=unknown_reason
                ).replace("[->", f"[{arguments_summary} ->")

                node_analysis.variables[result_name] = VariableTagInfo(
                    result_name, result_tag, operation_str
                )

            elif isinstance(operation, Return):
                for return_value in operation.values:
                    if return_value:
                        func_analysis.return_tags[get_var_name(return_value)] = get_tag(
                            domain, return_value
                        )

        func_analysis.nodes.append(node_analysis)

    # Override return tags based on function name
    if func_analysis.expected_tag:
        func_analysis.return_tags = {
            k: func_analysis.expected_tag for k in func_analysis.return_tags
        }

    return func_analysis


def display_function_analysis(func_analysis: FunctionAnalysis) -> None:
    """Display analysis results for a function."""
    console.print()
    console.print("=" * 80)
    console.print(
        f"[bold cyan]Function:[/bold cyan] [bold]{func_analysis.contract_name}.{func_analysis.function_name}[/bold]"
    )
    if func_analysis.expected_tag:
        console.print(
            f"[bold]Expected rounding:[/bold] {format_tag(func_analysis.expected_tag)} (inferred from function name)"
        )
    console.print("=" * 80)

    for node_analysis in func_analysis.nodes:
        if not node_analysis.variables:
            continue

        header = f"[bold]Node {node_analysis.node_id}:[/bold] {node_analysis.node_type}"
        console.print(header)
        if node_analysis.expression:
            console.print(f"[dim]Expression: {node_analysis.expression}[/dim]")

        table = Table(
            show_header=True, header_style="bold magenta", box=box.ROUNDED, show_lines=True
        )
        table.add_column("Variable", style="bold", width=25)
        table.add_column("Rounding Tag", justify="center", width=20)
        table.add_column("Operation", style="dim", width=35)

        for var_name, var_info in sorted(node_analysis.variables.items()):
            table.add_row(var_name, format_tag(var_info.tag), var_info.operation or "-")
        console.print(table)

    if func_analysis.return_tags:
        console.print("\n[bold]Return Values:[/bold]")
        return_table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
        return_table.add_column("Return Variable", style="bold")
        return_table.add_column("Rounding Tag", justify="center")

        for var_name, return_tag in func_analysis.return_tags.items():
            return_table.add_row(var_name, format_tag(return_tag))
            if func_analysis.expected_tag and return_tag != func_analysis.expected_tag:
                message_type = "WARNING" if return_tag == RoundingTag.UNKNOWN else "ERROR"
                color = "yellow" if return_tag == RoundingTag.UNKNOWN else "red"
                return_table.add_row(
                    "",
                    f"[{color}]✗ {message_type}:[/{color}] Expected {format_tag(func_analysis.expected_tag)}, got {format_tag(return_tag)}",
                )
        console.print(return_table)

    if func_analysis.inconsistencies:
        console.print("\n[bold red]Rounding Inconsistencies Detected:[/bold red]")
        for inconsistency in func_analysis.inconsistencies:
            console.print(f"[red]✗[/red] {inconsistency}")

    console.print()


def display_summary_table(analyses: List[FunctionAnalysis]) -> None:
    """Display summary table of all functions."""
    console.print("\n[bold cyan]" + "=" * 80)
    console.print("SUMMARY: All Functions")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED, show_lines=True)
    table.add_column("Function", style="bold", width=30)
    table.add_column("Expected", justify="center", width=15)
    table.add_column("Return Tag", justify="center", width=15)
    table.add_column("Status", justify="center", width=20)

    for func_analysis in analyses:
        function_name = f"{func_analysis.contract_name}.{func_analysis.function_name}"
        expected_tag_str = (
            format_tag(func_analysis.expected_tag) if func_analysis.expected_tag else "-"
        )
        return_tag = (
            list(func_analysis.return_tags.values())[0] if func_analysis.return_tags else None
        )
        return_tag_str = format_tag(return_tag) if return_tag else "-"

        if func_analysis.expected_tag and return_tag:
            status = (
                "[green]✓ MATCH[/green]"
                if return_tag == func_analysis.expected_tag
                else (
                    "[yellow]⚠ UNKNOWN[/yellow]"
                    if return_tag == RoundingTag.UNKNOWN
                    else "[red]✗ MISMATCH[/red]"
                )
            )
        else:
            status = "[dim]-[/dim]"

        table.add_row(function_name, expected_tag_str, return_tag_str, status)
    console.print(table)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[red]Usage:[/red] python test_rounding.py <contract_file> [function_name]")
        sys.exit(1)

    contract_path = Path(sys.argv[1])
    if not contract_path.exists():
        console.print(f"[red]Error:[/red] File not found: {contract_path}")
        sys.exit(1)

    function_analyses = []
    slither = Slither(str(contract_path))
    for contract in slither.contracts:
        for function in contract.functions:
            if isinstance(function, FunctionContract) and function.is_implemented:
                try:
                    function_analyses.append(analyze_function(function))
                except Exception as e:
                    console.print(f"[red]Error analyzing {function.name}:[/red] {e}")

    if not function_analyses:
        console.print("[yellow]No functions found to analyze[/yellow]")
        return

    if len(sys.argv) >= 3:
        requested_function_name = sys.argv[2]
        function_analyses = [
            analysis
            for analysis in function_analyses
            if analysis.function_name == requested_function_name
        ]
        if not function_analyses:
            console.print(f"[yellow]Function '{requested_function_name}' not found[/yellow]")
            return

    for func_analysis in function_analyses:
        display_function_analysis(func_analysis)

    if len(function_analyses) > 1:
        display_summary_table(function_analyses)


if __name__ == "__main__":
    main()
