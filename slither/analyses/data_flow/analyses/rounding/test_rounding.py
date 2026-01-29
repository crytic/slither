"""Visualization tool for rounding direction analysis."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

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
    """Rounding tag info for a variable with its producing operation."""

    name: str
    tag: RoundingTag
    operation: Optional[str] = None


@dataclass
class NodeAnalysis:
    """Analysis results for a single CFG node."""

    node_id: int
    node_type: str
    expression: Optional[str] = None
    variables: Dict[str, VariableTagInfo] = field(default_factory=dict)


@dataclass
class FunctionAnalysis:
    """Complete analysis results for a function."""

    function_name: str
    contract_name: str
    nodes: List[NodeAnalysis] = field(default_factory=list)
    return_tags: Dict[str, RoundingTag] = field(default_factory=dict)
    inconsistencies: List[str] = field(default_factory=list)
    annotation_mismatches: List[str] = field(default_factory=list)


@dataclass
class OperationContext:
    """Context for building operation display strings."""

    result_name: str
    result_tag: RoundingTag
    op_str: str
    left_name: str = ""
    left_tag: RoundingTag = RoundingTag.NEUTRAL
    right_name: str = ""
    right_tag: RoundingTag = RoundingTag.NEUTRAL
    unknown_reason: Optional[str] = None
    extra_note: str = ""


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


def build_operation_str(ctx: OperationContext) -> str:
    """Build operation string with tag information."""
    tag_parts = []
    if ctx.left_name:
        tag_parts.append(f"{ctx.left_name}:{ctx.left_tag.name}")
    if ctx.right_name:
        tag_parts.append(f"{ctx.right_name}:{ctx.right_tag.name}")

    if tag_parts:
        tags_str = f"[{', '.join(tag_parts)} -> {ctx.result_name}:{ctx.result_tag.name}]"
    else:
        tags_str = f"[-> {ctx.result_name}:{ctx.result_tag.name}]"

    result = f"{ctx.op_str} {tags_str}"
    if ctx.extra_note:
        result += f" ({ctx.extra_note})"
    if ctx.unknown_reason:
        result += f" (UNKNOWN: {ctx.unknown_reason})"
    return result


def _process_binary_op(domain: RoundingDomain, op: Binary, node_analysis: NodeAnalysis) -> None:
    """Process binary operation and add to node analysis."""
    left_name, left_tag, right_name, right_tag, result_name, result_tag = (
        extract_binary_info(domain, op)
    )
    unknown_reason = (
        get_unknown_reason(domain, op.lvalue, result_tag)
        if isinstance(op.lvalue, Variable)
        else None
    )

    operator_symbol = {
        BinaryType.ADDITION: "+",
        BinaryType.SUBTRACTION: "-",
        BinaryType.MULTIPLICATION: "*",
        BinaryType.DIVISION: "/",
    }.get(op.type, str(op.type.value))
    operation_string = f"{result_name} = {left_name} {operator_symbol} {right_name}"

    annotation = ""
    if op.type == BinaryType.DIVISION:
        annotation = (
            "inferred from ceiling division pattern as UP"
            if result_tag == RoundingTag.UP
            else "inferred from denominator inversion"
        )

    ctx = OperationContext(
        result_name=result_name,
        result_tag=result_tag,
        op_str=operation_string,
        left_name=left_name,
        left_tag=left_tag,
        right_name=right_name,
        right_tag=right_tag,
        unknown_reason=unknown_reason,
        extra_note=annotation,
    )
    node_analysis.variables[result_name] = VariableTagInfo(
        result_name, result_tag, build_operation_str(ctx)
    )


def _process_assignment_op(
    domain: RoundingDomain, op: Assignment, node_analysis: NodeAnalysis
) -> None:
    """Process assignment and add to node analysis."""
    rvalue_name, rvalue_tag, lvalue_name, lvalue_tag = extract_assignment_info(domain, op)
    unknown_reason = (
        get_unknown_reason(domain, op.lvalue, lvalue_tag)
        if isinstance(op.lvalue, Variable)
        else None
    )

    ctx = OperationContext(
        result_name=lvalue_name,
        result_tag=lvalue_tag,
        op_str=f"{lvalue_name} = {rvalue_name}",
        left_name=rvalue_name,
        left_tag=rvalue_tag,
        unknown_reason=unknown_reason,
    )
    node_analysis.variables[lvalue_name] = VariableTagInfo(
        lvalue_name, lvalue_tag, build_operation_str(ctx)
    )


def _process_call_op(
    domain: RoundingDomain,
    op: Union[InternalCall, HighLevelCall, LibraryCall],
    node_analysis: NodeAnalysis,
) -> None:
    """Process function call and add to node analysis."""
    result_name = get_var_name(op.lvalue)
    result_tag = get_tag(domain, op.lvalue)
    unknown_reason = (
        get_unknown_reason(domain, op.lvalue, result_tag)
        if isinstance(op.lvalue, Variable)
        else None
    )
    called_function_name = get_function_name(op)

    argument_tags = [
        f"{get_var_name(arg)}:{get_tag(domain, arg).name}" for arg in op.arguments
    ]
    arguments_summary = ", ".join(argument_tags) if argument_tags else "no-args"
    operation_string = f"{result_name} = {called_function_name}(...)"

    ctx = OperationContext(
        result_name=result_name,
        result_tag=result_tag,
        op_str=operation_string,
        unknown_reason=unknown_reason,
    )
    operation_str = build_operation_str(ctx).replace("[->", f"[{arguments_summary} ->")
    node_analysis.variables[result_name] = VariableTagInfo(result_name, result_tag, operation_str)


def _process_return_op(
    domain: RoundingDomain, op: Return, func_analysis: FunctionAnalysis
) -> None:
    """Process return operation and update function analysis."""
    for return_value in op.values:
        if return_value:
            func_analysis.return_tags[get_var_name(return_value)] = get_tag(domain, return_value)


def analyze_function(function: FunctionContract) -> FunctionAnalysis:
    """Analyze a function and extract all variable rounding tags."""
    func_analysis = FunctionAnalysis(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
    )

    rounding_analysis = RoundingAnalysis()
    engine = Engine.new(rounding_analysis, function)
    engine.run_analysis()
    node_results: Dict[Node, AnalysisState] = engine.result()
    func_analysis.inconsistencies = rounding_analysis.inconsistencies
    func_analysis.annotation_mismatches = rounding_analysis.annotation_mismatches

    for node in function.nodes:
        if node not in node_results or node_results[node].post.variant != DomainVariant.STATE:
            continue

        domain = node_results[node].post
        node_analysis = NodeAnalysis(
            node_id=node.node_id,
            node_type=node.type.name,
            expression=str(node.expression) if node.expression else None,
        )

        if node.irs_ssa:
            for operation in node.irs_ssa:
                if isinstance(operation, Binary) and operation.lvalue:
                    _process_binary_op(domain, operation, node_analysis)
                elif isinstance(operation, Assignment) and operation.lvalue:
                    _process_assignment_op(domain, operation, node_analysis)
                elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)):
                    if operation.lvalue:
                        _process_call_op(domain, operation, node_analysis)
                elif isinstance(operation, Return):
                    _process_return_op(domain, operation, func_analysis)

        func_analysis.nodes.append(node_analysis)

    return func_analysis


def _display_node_table(node_analysis: NodeAnalysis) -> None:
    """Display variable table for a single node."""
    header = f"[bold]Node {node_analysis.node_id}:[/bold] {node_analysis.node_type}"
    console.print(header)
    if node_analysis.expression:
        console.print(f"[dim]Expression: {node_analysis.expression}[/dim]")

    table = Table(
        show_header=True, header_style="bold magenta", box=box.ROUNDED, show_lines=True
    )
    table.add_column("Variable", style="bold", width=25)
    table.add_column("Rounding Tag", justify="center", width=20)
    table.add_column("Operation", style="dim", overflow="fold")

    for var_name, var_info in sorted(node_analysis.variables.items()):
        operation_text = Text(var_info.operation) if var_info.operation else Text("-")
        table.add_row(var_name, format_tag(var_info.tag), operation_text)
    console.print(table)


def _display_return_values(func_analysis: FunctionAnalysis) -> None:
    """Display return value tags if present."""
    if not func_analysis.return_tags:
        return

    console.print("\n[bold]Return Values:[/bold]")
    return_table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
    return_table.add_column("Return Variable", style="bold")
    return_table.add_column("Rounding Tag", justify="center")

    for var_name, return_tag in func_analysis.return_tags.items():
        return_table.add_row(var_name, format_tag(return_tag))
    console.print(return_table)


def _display_issues(func_analysis: FunctionAnalysis) -> None:
    """Display inconsistencies and annotation mismatches."""
    if func_analysis.inconsistencies:
        console.print("\n[bold red]Rounding Inconsistencies Detected:[/bold red]")
        for inconsistency in func_analysis.inconsistencies:
            console.print(f"[red]✗[/red] {inconsistency}")

    if func_analysis.annotation_mismatches:
        console.print("\n[bold red]Rounding Annotation Mismatches Detected:[/bold red]")
        for mismatch in func_analysis.annotation_mismatches:
            console.print(f"[red]✗[/red] {mismatch}")


def display_function_analysis(func_analysis: FunctionAnalysis) -> None:
    """Display analysis results for a function."""
    console.print()
    console.print("=" * 80)
    func_label = f"{func_analysis.contract_name}.{func_analysis.function_name}"
    console.print(f"[bold cyan]Function:[/bold cyan] [bold]{func_label}[/bold]")
    console.print("=" * 80)

    for node_analysis in func_analysis.nodes:
        if node_analysis.variables:
            _display_node_table(node_analysis)

    _display_return_values(func_analysis)
    _display_issues(func_analysis)
    console.print()


def display_summary_table(analyses: List[FunctionAnalysis]) -> None:
    """Display summary table of all functions."""
    console.print("\n[bold cyan]" + "=" * 80)
    console.print("SUMMARY: All Functions")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED, show_lines=True)
    table.add_column("Function", style="bold", width=30)
    table.add_column("Return Tag", justify="center", width=15)

    for func_analysis in analyses:
        function_name = f"{func_analysis.contract_name}.{func_analysis.function_name}"
        return_tag = (
            list(func_analysis.return_tags.values())[0] if func_analysis.return_tags else None
        )
        return_tag_str = format_tag(return_tag) if return_tag else "-"

        table.add_row(function_name, return_tag_str)
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
