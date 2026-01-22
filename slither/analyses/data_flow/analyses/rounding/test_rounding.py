"""Visualization tool for rounding direction analysis.

Shows all variables and their rounding tags (UP/DOWN/UNKNOWN) per function,
making it easy to see where variables are going in terms of rounding direction.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import RoundingAnalysis
from slither.analyses.data_flow.analyses.rounding.analysis.domain import DomainVariant
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.library_call import LibraryCall

console = Console()


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class VariableTagInfo:
    """Information about a variable's rounding tag."""

    name: str
    tag: RoundingTag
    operation: Optional[str] = None
    source_vars: List[str] = field(default_factory=list)


@dataclass
class NodeAnalysis:
    """Analysis results for a single node."""

    node_id: int
    node_type: str
    expression: Optional[str] = None
    variables: Dict[str, VariableTagInfo] = field(default_factory=dict)
    operations: List[str] = field(default_factory=list)


@dataclass
class FunctionAnalysis:
    """Complete analysis for a function."""

    function_name: str
    contract_name: str
    nodes: List[NodeAnalysis] = field(default_factory=list)
    return_tags: Dict[str, RoundingTag] = field(default_factory=dict)
    expected_tag: Optional[RoundingTag] = None


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================


def format_tag(tag: RoundingTag) -> str:
    """Format rounding tag with emoji and color."""
    formats = {
        RoundingTag.UP: ("🔼 UP", "green"),
        RoundingTag.DOWN: ("🔽 DOWN", "red"),
        RoundingTag.UNKNOWN: ("❓ UNKNOWN", "yellow"),
    }
    text, color = formats.get(tag, (str(tag), "white"))
    return f"[{color}]{text}[/{color}]"


def get_variable_name(var) -> str:
    """Get a readable name for a variable."""
    if hasattr(var, "name"):
        return var.name
    return str(var)


def analyze_function(function: FunctionContract) -> FunctionAnalysis:
    """Analyze a function and extract all variable rounding tags."""
    result = FunctionAnalysis(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
    )

    # Infer expected rounding from function name
    func_name_lower = function.name.lower()
    if "down" in func_name_lower or "floor" in func_name_lower:
        result.expected_tag = RoundingTag.DOWN
    elif "up" in func_name_lower or "ceil" in func_name_lower:
        result.expected_tag = RoundingTag.UP

    # Run analysis
    analysis = RoundingAnalysis()
    engine = Engine.new(analysis, function)
    engine.run_analysis()
    results: Dict[Node, AnalysisState] = engine.result()

    # Process each node
    for node in function.nodes:
        if node not in results:
            continue

        state = results[node]
        if state.post.variant != DomainVariant.STATE:
            continue

        domain = state.post
        # Get expression string
        expression_str = str(node.expression) if node.expression else None
        node_analysis = NodeAnalysis(
            node_id=node.node_id,
            node_type=node.type.name,
            expression=expression_str,
        )

        # Collect variables from operations in this node
        if node.irs_ssa:
            for ir in node.irs_ssa:
                # Handle binary operations
                if isinstance(ir, Binary):
                    left = ir.variable_left
                    right = ir.variable_right
                    result_var = ir.lvalue

                    if result_var:
                        left_name = get_variable_name(left) if left else "?"
                        right_name = get_variable_name(right) if right else "?"
                        result_name = get_variable_name(result_var)

                        left_tag = (
                            domain.state.get_tag(left)
                            if left and hasattr(left, "name")
                            else RoundingTag.UNKNOWN
                        )
                        right_tag = (
                            domain.state.get_tag(right)
                            if right and hasattr(right, "name")
                            else RoundingTag.UNKNOWN
                        )
                        result_tag = domain.state.get_tag(result_var)

                        op_symbol = {
                            BinaryType.ADDITION: "+",
                            BinaryType.SUBTRACTION: "-",
                            BinaryType.MULTIPLICATION: "*",
                            BinaryType.DIVISION: "/",
                        }.get(ir.type, str(ir.type.value))

                        operation_str = f"{result_name} = {left_name} {op_symbol} {right_name}"
                        node_analysis.operations.append(operation_str)

                        node_analysis.variables[result_name] = VariableTagInfo(
                            name=result_name,
                            tag=result_tag,
                            operation=operation_str,
                            source_vars=[left_name, right_name] if left_name != "?" else [],
                        )

                        # Also track source variables if they're not already tracked
                        if left and hasattr(left, "name") and left_name not in node_analysis.variables:
                            node_analysis.variables[left_name] = VariableTagInfo(
                                name=left_name, tag=left_tag
                            )
                        if right and hasattr(right, "name") and right_name not in node_analysis.variables:
                            node_analysis.variables[right_name] = VariableTagInfo(
                                name=right_name, tag=right_tag
                            )

                # Handle assignments
                elif isinstance(ir, Assignment):
                    rvalue = ir.rvalue
                    lvalue = ir.lvalue

                    if lvalue:
                        rvalue_name = get_variable_name(rvalue) if rvalue else "?"
                        lvalue_name = get_variable_name(lvalue)

                        rvalue_tag = (
                            domain.state.get_tag(rvalue)
                            if rvalue and hasattr(rvalue, "name")
                            else RoundingTag.UNKNOWN
                        )
                        lvalue_tag = domain.state.get_tag(lvalue)

                        operation_str = f"{lvalue_name} = {rvalue_name}"
                        node_analysis.operations.append(operation_str)

                        node_analysis.variables[lvalue_name] = VariableTagInfo(
                            name=lvalue_name,
                            tag=lvalue_tag,
                            operation=operation_str,
                            source_vars=[rvalue_name] if rvalue_name != "?" else [],
                        )

                        if rvalue and hasattr(rvalue, "name") and rvalue_name not in node_analysis.variables:
                            node_analysis.variables[rvalue_name] = VariableTagInfo(
                                name=rvalue_name, tag=rvalue_tag
                            )

                # Handle function calls
                elif isinstance(ir, (InternalCall, HighLevelCall, LibraryCall)):
                    result_var = ir.lvalue
                    if result_var:
                        result_name = get_variable_name(result_var)
                        result_tag = domain.state.get_tag(result_var)

                        # Get function name
                        if isinstance(ir, InternalCall):
                            func_name = ir.function.name if ir.function else str(ir.function_name)
                        else:
                            func_name = (
                                ir.function_name.value
                                if hasattr(ir.function_name, "value")
                                else str(ir.function_name)
                            )

                        operation_str = f"{result_name} = {func_name}(...)"
                        node_analysis.operations.append(operation_str)

                        node_analysis.variables[result_name] = VariableTagInfo(
                            name=result_name,
                            tag=result_tag,
                            operation=operation_str,
                        )

                # Handle return statements
                elif isinstance(ir, Return):
                    for val in ir.values:
                        val_name = get_variable_name(val) if val else "?"
                        val_tag = (
                            domain.state.get_tag(val)
                            if val and hasattr(val, "name")
                            else RoundingTag.UNKNOWN
                        )
                        result.return_tags[val_name] = val_tag

        result.nodes.append(node_analysis)

    return result


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================


def display_function_analysis(func_analysis: FunctionAnalysis) -> None:
    """Display analysis results for a function using rich formatting."""
    console.print()
    console.print("=" * 80)
    console.print(
        f"[bold cyan]Function:[/bold cyan] [bold]{func_analysis.contract_name}.{func_analysis.function_name}[/bold]"
    )

    # Show expected rounding if function name implies one
    if func_analysis.expected_tag:
        console.print(
            f"[bold]Expected rounding:[/bold] {format_tag(func_analysis.expected_tag)} "
            f"(inferred from function name)"
        )

    console.print("=" * 80)

    # Display variables table for each node
    for node_analysis in func_analysis.nodes:
        if not node_analysis.variables:
            continue

        # Get the actual node to access expression
        node_obj = None
        for contract in func_analysis._contract.functions if hasattr(func_analysis, '_contract') else []:
            # We need to find the node - let's store it in the analysis
            pass
        
        node_header = f"[bold]Node {node_analysis.node_id}:[/bold] {node_analysis.node_type}"
        if node_analysis.expression:
            console.print(node_header)
            console.print(f"[dim]Expression: {node_analysis.expression}[/dim]")
        else:
            console.print(node_header)

        # Create table for variables
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            show_lines=True,
        )
        table.add_column("Variable", style="bold", width=25)
        table.add_column("Rounding Tag", justify="center", width=20)
        table.add_column("Operation", style="dim", width=35)

        # Sort variables by name for consistency
        sorted_vars = sorted(node_analysis.variables.items())

        for var_name, var_info in sorted_vars:
            operation_str = var_info.operation or "-"
            table.add_row(var_name, format_tag(var_info.tag), operation_str)

        console.print(table)

    # Show return summary
    if func_analysis.return_tags:
        console.print("\n[bold]Return Values:[/bold]")
        return_table = Table(
            show_header=True,
            header_style="bold green",
            box=box.ROUNDED,
        )
        return_table.add_column("Return Variable", style="bold")
        return_table.add_column("Rounding Tag", justify="center")

        for var_name, tag in func_analysis.return_tags.items():
            return_table.add_row(var_name, format_tag(tag))

            # Check for mismatch if expected tag is set
            if func_analysis.expected_tag and tag != func_analysis.expected_tag:
                if tag == RoundingTag.UNKNOWN:
                    mismatch_msg = f"[yellow]⚠ WARNING:[/yellow] Expected {format_tag(func_analysis.expected_tag)}, got {format_tag(tag)}"
                else:
                    mismatch_msg = f"[red]✗ ERROR:[/red] Expected {format_tag(func_analysis.expected_tag)}, got {format_tag(tag)}"
                return_table.add_row("", mismatch_msg)

        console.print(return_table)

    console.print()


def display_summary_table(analyses: List[FunctionAnalysis]) -> None:
    """Display a summary table of all functions."""
    console.print("\n[bold cyan]" + "=" * 80)
    console.print("SUMMARY: All Functions")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    summary_table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        show_lines=True,
    )
    summary_table.add_column("Function", style="bold", width=30)
    summary_table.add_column("Expected", justify="center", width=15)
    summary_table.add_column("Return Tag", justify="center", width=15)
    summary_table.add_column("Status", justify="center", width=20)

    for func_analysis in analyses:
        func_name = f"{func_analysis.contract_name}.{func_analysis.function_name}"

        expected_str = (
            format_tag(func_analysis.expected_tag) if func_analysis.expected_tag else "-"
        )

        # Get return tag (use first return value if multiple)
        return_tag = (
            list(func_analysis.return_tags.values())[0] if func_analysis.return_tags else None
        )
        return_str = format_tag(return_tag) if return_tag else "-"

        # Determine status
        if func_analysis.expected_tag and return_tag:
            if return_tag == func_analysis.expected_tag:
                status = "[green]✓ MATCH[/green]"
            elif return_tag == RoundingTag.UNKNOWN:
                status = "[yellow]⚠ UNKNOWN[/yellow]"
            else:
                status = "[red]✗ MISMATCH[/red]"
        else:
            status = "[dim]-[/dim]"

        summary_table.add_row(func_name, expected_str, return_str, status)

    console.print(summary_table)


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================


def analyze_contract(contract_path: Path) -> List[FunctionAnalysis]:
    """Analyze all functions in a contract file."""
    slither = Slither(str(contract_path))
    analyses = []

    for contract in slither.contracts:
        for function in contract.functions:
            if isinstance(function, FunctionContract) and function.is_implemented:
                try:
                    analysis = analyze_function(function)
                    analyses.append(analysis)
                except Exception as e:
                    console.print(f"[red]Error analyzing {function.name}:[/red] {e}")

    return analyses


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[red]Usage:[/red] python test_rounding.py <contract_file> [function_name]")
        console.print(
            "  If function_name is provided, only show that function's analysis"
        )
        sys.exit(1)

    contract_path = Path(sys.argv[1])
    if not contract_path.exists():
        console.print(f"[red]Error:[/red] File not found: {contract_path}")
        sys.exit(1)

    # Analyze contract
    analyses = analyze_contract(contract_path)

    if not analyses:
        console.print("[yellow]No functions found to analyze[/yellow]")
        return

    # Filter by function name if provided
    if len(sys.argv) >= 3:
        function_name = sys.argv[2]
        analyses = [a for a in analyses if a.function_name == function_name]
        if not analyses:
            console.print(f"[yellow]Function '{function_name}' not found[/yellow]")
            return

    # Display results
    for analysis in analyses:
        display_function_analysis(analysis)

    # Show summary if multiple functions
    if len(analyses) > 1:
        display_summary_table(analyses)


if __name__ == "__main__":
    main()
