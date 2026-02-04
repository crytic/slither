"""Visualization tool for rounding direction analysis."""

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.text import Text

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import RoundingAnalysis
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag, TagSet
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node, NodeType
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
logger = get_logger()


@dataclass
class LineAnnotation:
    """Annotation for a single variable on a source line."""

    variable_name: str
    tags: TagSet
    is_return: bool = False
    note: str = ""


@dataclass
class AnnotatedLine:
    """Source line with its annotations."""

    line_number: int
    source_text: str
    annotations: list[LineAnnotation] = field(default_factory=list)
    is_entry: bool = False


@dataclass
class AnnotatedFunction:
    """Complete annotated source view for a function."""

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    lines: dict[int, AnnotatedLine] = field(default_factory=dict)
    return_tags: dict[str, TagSet] = field(default_factory=dict)
    inconsistencies: list[str] = field(default_factory=list)
    annotation_mismatches: list[str] = field(default_factory=list)


def get_variable_name(variable: Optional[Union[RVALUE, Variable]]) -> str:
    """Get variable name, or string representation if not a Variable."""
    if isinstance(variable, Variable):
        return variable.name
    return str(variable) if variable else "?"


def get_tags(
    domain: RoundingDomain,
    variable: Optional[Union[RVALUE, Variable]],
) -> TagSet:
    """Get rounding tags for a variable."""
    if isinstance(variable, Variable):
        return domain.state.get_tags(variable)
    return frozenset({RoundingTag.NEUTRAL})


def get_unknown_reason(
    domain: RoundingDomain,
    variable: Variable,
    tags: TagSet,
) -> Optional[str]:
    """Get unknown reason if tags include UNKNOWN."""
    if RoundingTag.UNKNOWN in tags:
        return domain.state.get_unknown_reason(variable)
    return None


def format_tag_inline(tags: TagSet) -> Text:
    """Format rounding tag set with color."""
    colors = {
        RoundingTag.UP: "green",
        RoundingTag.DOWN: "red",
        RoundingTag.NEUTRAL: "white",
        RoundingTag.UNKNOWN: "yellow",
    }
    if len(tags) == 1:
        tag = next(iter(tags))
        return Text(tag.name, style=colors.get(tag, "white"))
    names = sorted(tag.name for tag in tags)
    return Text("{" + ", ".join(names) + "}", style="yellow")


def read_source_lines(filename: str, start_line: int, end_line: int) -> dict[int, str]:
    """Read source file lines within the given range."""
    lines: dict[int, str] = {}
    try:
        with open(filename, encoding="utf-8") as source_file:
            for line_index, line in enumerate(source_file, start=1):
                if start_line <= line_index <= end_line:
                    lines[line_index] = line.rstrip("\n\r")
                if line_index > end_line:
                    break
    except (OSError, UnicodeDecodeError):
        pass
    return lines


def get_node_line(node: Node) -> Optional[int]:
    """Get the primary source line for a node."""
    if node.source_mapping and node.source_mapping.lines:
        return node.source_mapping.lines[0]
    return None


def build_annotation_note(operation: Binary, result_tags: TagSet) -> str:
    """Build annotation note for division operations."""
    if operation.type != BinaryType.DIVISION:
        return ""
    if result_tags == frozenset({RoundingTag.UP}):
        return "ceiling pattern"
    if result_tags == frozenset({RoundingTag.DOWN}):
        return "floor division"
    return ""


def analyze_function(
    function: FunctionContract,
    show_all: bool = False,
) -> AnnotatedFunction:
    """Analyze a function and build annotated source view."""
    annotated = _create_annotated_function(function)
    _populate_source_lines(annotated)

    analysis = RoundingAnalysis()
    engine = Engine.new(analysis, function)
    engine.run_analysis()
    node_results: dict[Node, AnalysisState] = engine.result()

    annotated.inconsistencies = analysis.inconsistencies
    annotated.annotation_mismatches = analysis.annotation_mismatches

    _process_node_results(function, node_results, annotated, show_all)
    return annotated


def _create_annotated_function(function: FunctionContract) -> AnnotatedFunction:
    """Create initial AnnotatedFunction from function metadata."""
    source_mapping = function.source_mapping
    filename = source_mapping.filename.absolute if source_mapping else ""
    start_line = source_mapping.lines[0] if source_mapping and source_mapping.lines else 0
    end_line = source_mapping.lines[-1] if source_mapping and source_mapping.lines else 0

    return AnnotatedFunction(
        function_name=function.name,
        contract_name=function.contract.name if function.contract else "Unknown",
        filename=filename,
        start_line=start_line,
        end_line=end_line,
    )


def _populate_source_lines(annotated: AnnotatedFunction) -> None:
    """Populate annotated function with source lines."""
    source_lines = read_source_lines(
        annotated.filename, annotated.start_line, annotated.end_line
    )
    for line_num, text in source_lines.items():
        annotated.lines[line_num] = AnnotatedLine(
            line_number=line_num,
            source_text=text,
        )


def _process_node_results(
    function: FunctionContract,
    node_results: dict[Node, AnalysisState],
    annotated: AnnotatedFunction,
    show_all: bool = False,
) -> None:
    """Process analysis results and add annotations to lines."""
    for node in function.nodes:
        if node not in node_results:
            continue
        if node_results[node].post.variant != DomainVariant.STATE:
            continue

        domain = node_results[node].post
        line_num = get_node_line(node)

        if node.type == NodeType.ENTRYPOINT and line_num and line_num in annotated.lines:
            annotated.lines[line_num].is_entry = True
            if show_all:
                _add_parameter_annotations(function, domain, annotated.lines[line_num])

        if line_num is None or line_num not in annotated.lines:
            continue

        annotated_line = annotated.lines[line_num]
        if node.irs_ssa:
            for operation in node.irs_ssa:
                _process_operation(operation, domain, annotated_line, annotated)


def _add_parameter_annotations(
    function: FunctionContract,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Add annotations for function parameters."""
    for parameter in function.parameters:
        tags = get_tags(domain, parameter)
        annotated_line.annotations.append(
            LineAnnotation(variable_name=parameter.name, tags=tags, note="parameter")
        )


def _process_operation(
    operation: Union[Binary, Assignment, InternalCall, HighLevelCall, LibraryCall, Return],
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
    annotated: AnnotatedFunction,
) -> None:
    """Process an operation and add annotations."""
    if isinstance(operation, Binary) and operation.lvalue:
        _process_binary_operation(operation, domain, annotated_line)
    elif isinstance(operation, Assignment) and operation.lvalue:
        _process_assignment_operation(operation, domain, annotated_line)
    elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)) and operation.lvalue:
        _process_call_operation(operation, domain, annotated_line)
    elif isinstance(operation, Return):
        _process_return_operation(operation, domain, annotated_line, annotated)


def _process_binary_operation(
    operation: Binary,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process binary operation."""
    result_name = get_variable_name(operation.lvalue)
    result_tags = get_tags(domain, operation.lvalue)

    if isinstance(operation.lvalue, Variable):
        unknown_reason = get_unknown_reason(domain, operation.lvalue, result_tags)
        if unknown_reason:
            note = unknown_reason
        else:
            note = _build_binary_reasoning(operation, domain, result_tags)
    else:
        note = build_annotation_note(operation, result_tags)

    annotated_line.annotations.append(
        LineAnnotation(variable_name=result_name, tags=result_tags, note=note)
    )


def _build_binary_reasoning(
    operation: Binary,
    domain: RoundingDomain,
    result_tags: TagSet,
) -> str:
    """Build reasoning note showing operand tags for binary operations."""
    left_tags = get_tags(domain, operation.variable_left)
    right_tags = get_tags(domain, operation.variable_right)
    left_name = get_variable_name(operation.variable_left)
    right_name = get_variable_name(operation.variable_right)

    op_symbol = _get_operation_symbol(operation.type)
    base_note = build_annotation_note(operation, result_tags)

    left_str = _format_tag_for_reasoning(left_tags)
    right_str = _format_tag_for_reasoning(right_tags)
    reasoning = f"{left_name}:{left_str} {op_symbol} {right_name}:{right_str}"
    if base_note:
        return f"{reasoning} ({base_note})"
    return reasoning


def _format_tag_for_reasoning(tags: TagSet) -> str:
    """Format tag set for display in reasoning notes."""
    if len(tags) == 1:
        return next(iter(tags)).name
    names = sorted(tag.name for tag in tags)
    return "{" + ", ".join(names) + "}"


def _get_operation_symbol(binary_type: BinaryType) -> str:
    """Get the symbol for a binary operation type."""
    symbols = {
        BinaryType.ADDITION: "+",
        BinaryType.SUBTRACTION: "-",
        BinaryType.MULTIPLICATION: "*",
        BinaryType.DIVISION: "/",
        BinaryType.MODULO: "%",
    }
    return symbols.get(binary_type, "?")


def _process_assignment_operation(
    operation: Assignment,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process assignment operation."""
    lvalue_name = get_variable_name(operation.lvalue)
    lvalue_tags = get_tags(domain, operation.lvalue)
    annotated_line.annotations.append(
        LineAnnotation(variable_name=lvalue_name, tags=lvalue_tags)
    )


def _process_call_operation(
    operation: Union[InternalCall, HighLevelCall, LibraryCall],
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process call operation."""
    result_name = get_variable_name(operation.lvalue)
    result_tags = get_tags(domain, operation.lvalue)
    func_name = _get_call_function_name(operation)
    note = f"from {func_name}()"
    annotated_line.annotations.append(
        LineAnnotation(variable_name=result_name, tags=result_tags, note=note)
    )


def _process_return_operation(
    operation: Return,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
    annotated: AnnotatedFunction,
) -> None:
    """Process return operation."""
    for return_value in operation.values:
        if not return_value:
            continue
        var_name = get_variable_name(return_value)
        tags = get_tags(domain, return_value)
        existing = annotated.return_tags.get(var_name, frozenset())
        annotated.return_tags[var_name] = existing | tags
        annotated_line.annotations.append(
            LineAnnotation(variable_name=var_name, tags=tags, is_return=True)
        )


def _get_call_function_name(
    operation: Union[InternalCall, HighLevelCall, LibraryCall]
) -> str:
    """Extract function name from call operation."""
    if isinstance(operation, InternalCall):
        return operation.function.name if operation.function else str(operation.function_name)
    return str(operation.function_name.value)


def display_annotated_source(annotated: AnnotatedFunction) -> None:
    """Display annotated source code view."""
    console.print()
    console.print("=" * 80)
    func_label = f"{annotated.contract_name}.{annotated.function_name}"
    console.print(f"[bold cyan]Function:[/bold cyan] [bold]{func_label}[/bold]")
    console.print("=" * 80)

    if annotated.filename:
        relative_path = _get_relative_path(annotated.filename)
        location = f"[{relative_path}:{annotated.start_line}:{annotated.end_line}]"
        console.print(Text(location, style="dim"))

    line_width = len(str(annotated.end_line))

    for line_num in range(annotated.start_line, annotated.end_line + 1):
        if line_num not in annotated.lines:
            continue
        annotated_line = annotated.lines[line_num]
        _display_source_line(annotated_line, line_width)
        _display_annotations(annotated_line, line_width)

    _display_return_summary(annotated)
    _display_issues(annotated)
    console.print()


def _get_relative_path(filename: str) -> str:
    """Get a shorter relative path for display."""
    path = Path(filename)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        parts = path.parts
        if len(parts) >= 2:
            return str(Path(*parts[-2:]))
        return path.name


def _display_source_line(annotated_line: AnnotatedLine, line_width: int) -> None:
    """Display a single source line with line number."""
    line_num_str = str(annotated_line.line_number).rjust(line_width)
    entry_marker = "[bold magenta]→[/bold magenta]" if annotated_line.is_entry else " "
    console.print(f"{line_num_str} {entry_marker} │ {annotated_line.source_text}")


def _display_annotations(annotated_line: AnnotatedLine, line_width: int) -> None:
    """Display annotations below a source line."""
    if not annotated_line.annotations:
        return

    padding = " " * line_width
    seen_vars: set[str] = set()

    for annotation in annotated_line.annotations:
        if annotation.variable_name in seen_vars:
            continue
        seen_vars.add(annotation.variable_name)

        prefix = "returns:" if annotation.is_return else ""
        var_display = f'"{annotation.variable_name}"'
        note_text = f" ({annotation.note})" if annotation.note else ""

        line = Text()
        line.append(f"{padding}   │     └── ", style="dim")
        if prefix:
            line.append(f"{prefix} ", style="bold")
        line.append(var_display, style="cyan")
        line.append(" → ")
        line.append(format_tag_inline(annotation.tags))
        if note_text:
            line.append(note_text, style="dim")

        console.print(line)


def _display_return_summary(annotated: AnnotatedFunction) -> None:
    """Display return value summary."""
    if not annotated.return_tags:
        return

    console.print()
    returns_line = Text()
    returns_line.append("Return Values: ", style="bold")

    items = []
    for var_name, tags in annotated.return_tags.items():
        filtered_tags = tags
        if len(filtered_tags) > 1 and RoundingTag.NEUTRAL in filtered_tags:
            filtered_tags = filtered_tags - {RoundingTag.NEUTRAL}
        item = Text()
        item.append(var_name, style="cyan")
        item.append(" → ")
        item.append(format_tag_inline(filtered_tags))
        items.append(item)

    for index, item in enumerate(items):
        if index > 0:
            returns_line.append(", ")
        returns_line.append(item)

    console.print(returns_line)


def _display_issues(annotated: AnnotatedFunction) -> None:
    """Display inconsistencies and annotation mismatches."""
    if annotated.inconsistencies:
        console.print()
        console.print("[bold red]Rounding Inconsistencies:[/bold red]")
        for inconsistency in annotated.inconsistencies:
            console.print(f"  [red]✗[/red] {inconsistency}")

    if annotated.annotation_mismatches:
        console.print()
        console.print("[bold red]Annotation Mismatches:[/bold red]")
        for mismatch in annotated.annotation_mismatches:
            console.print(f"  [red]✗[/red] {mismatch}")


def display_summary_table(analyses: list[AnnotatedFunction]) -> None:
    """Display summary of all analyzed functions."""
    console.print()
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]SUMMARY: All Functions[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()

    for func in analyses:
        func_name = f"{func.contract_name}.{func.function_name}"
        if func.return_tags:
            for var_name, tags in func.return_tags.items():
                filtered_tags = tags
                if len(filtered_tags) > 1 and RoundingTag.NEUTRAL in filtered_tags:
                    filtered_tags = filtered_tags - {RoundingTag.NEUTRAL}
                line = Text()
                line.append(f"  {func_name}", style="bold")
                line.append(f" returns {var_name} → ")
                line.append(format_tag_inline(filtered_tags))
                console.print(line)
        else:
            console.print(f"  [bold]{func_name}[/bold] [dim](no return)[/dim]")


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Rounding direction analysis visualization tool"
    )
    parser.add_argument("project_path", help="Path to Solidity file or project directory")
    parser.add_argument(
        "-c", "--contract",
        help="Filter by filename or exact contract name (e.g., LinearPool.sol or LinearPool)"
    )
    parser.add_argument("-f", "--function", help="Filter to this specific function name")
    parser.add_argument(
        "--all", action="store_true",
        help="Show all variables including NEUTRAL parameters"
    )
    return parser


def _collect_functions(
    slither_instance: Slither,
    contract_filter: Optional[str],
    function_filter: Optional[str],
) -> list[FunctionContract]:
    """Collect functions to analyze based on filters."""
    functions: list[FunctionContract] = []
    exact_name_exists = any(
        contract.name == contract_filter for contract in slither_instance.contracts
    )

    for contract in slither_instance.contracts:
        if contract_filter:
            if exact_name_exists:
                if contract.name != contract_filter:
                    continue
                function_source = contract.functions_declared
            else:
                contract_file = (
                    contract.source_mapping.filename.short if contract.source_mapping else ""
                )
                if contract_filter not in contract_file:
                    continue
                function_source = contract.functions
        else:
            function_source = contract.functions

        for function in function_source:
            if function_filter and function.name != function_filter:
                continue
            if isinstance(function, FunctionContract) and function.is_implemented:
                functions.append(function)
    return functions


def main() -> None:
    """Main entry point."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        logger.error_and_raise(f"Path not found: {project_path}", FileNotFoundError)

    slither_instance = Slither(str(project_path))
    functions = _collect_functions(slither_instance, args.contract, args.function)

    if not functions:
        logger.warning("No functions found to analyze")
        return

    function_analyses: list[AnnotatedFunction] = []
    for function in functions:
        try:
            function_analyses.append(analyze_function(function, show_all=args.all))
        except Exception as exception:
            logger.error(f"Error analyzing {function.name}: {exception}")

    if not function_analyses:
        logger.warning("No functions analyzed successfully")
        return

    for analysis in function_analyses:
        display_annotated_source(analysis)

    if len(function_analyses) > 1:
        display_summary_table(function_analyses)


if __name__ == "__main__":
    main()
