"""Visualization tool for rounding direction analysis."""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.text import Text

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import RoundingAnalysis
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.analysis.interprocedural import (
    RoundingInterproceduralAnalyzer,
    RoundingResult,
)
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
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


@dataclass
class LineAnnotation:
    """Annotation for a single variable on a source line."""

    variable_name: str
    tag: RoundingTag
    is_return: bool = False
    note: str = ""


@dataclass
class AnnotatedLine:
    """Source line with its annotations."""

    line_number: int
    source_text: str
    annotations: list[LineAnnotation] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False


@dataclass
class AnnotatedFunction:
    """Complete annotated source view for a function."""

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    lines: dict[int, AnnotatedLine] = field(default_factory=dict)
    return_tags: dict[str, RoundingTag] = field(default_factory=dict)
    inconsistencies: list[str] = field(default_factory=list)
    annotation_mismatches: list[str] = field(default_factory=list)
    path_traces: list[str] = field(default_factory=list)  # Interprocedural path traces
    query_tag: Optional[RoundingTag] = None  # Tag being queried


def get_variable_name(variable: Optional[Union[RVALUE, Variable]]) -> str:
    """Get variable name, or string representation if not a Variable."""
    if isinstance(variable, Variable):
        return variable.name
    return str(variable) if variable else "?"


def get_tag(domain: RoundingDomain, variable: Optional[Union[RVALUE, Variable]]) -> RoundingTag:
    """Get rounding tag for a variable, defaulting to NEUTRAL for non-variables."""
    if isinstance(variable, Variable):
        return domain.state.get_tag(variable)
    return RoundingTag.NEUTRAL


def get_unknown_reason(
    domain: RoundingDomain, variable: Variable, tag: RoundingTag
) -> Optional[str]:
    """Get unknown reason if tag is UNKNOWN."""
    if tag == RoundingTag.UNKNOWN:
        return domain.state.get_unknown_reason(variable)
    return None


def format_tag_inline(tag: RoundingTag) -> Text:
    """Format rounding tag with color for inline display."""
    colors = {
        RoundingTag.UP: "green",
        RoundingTag.DOWN: "red",
        RoundingTag.NEUTRAL: "white",
        RoundingTag.UNKNOWN: "yellow",
    }
    color = colors.get(tag, "white")
    return Text(tag.name, style=color)


def format_tags_set(tags: set[RoundingTag]) -> Text:
    """Format a set of rounding tags with colors."""
    result = Text("{")
    sorted_tags = sorted(tags, key=lambda t: t.name)
    for i, tag in enumerate(sorted_tags):
        if i > 0:
            result.append(", ")
        result.append(format_tag_inline(tag))
    result.append("}")
    return result


def read_source_lines(filename: str, start_line: int, end_line: int) -> dict[int, str]:
    """Read source file lines within the given range."""
    lines: dict[int, str] = {}
    try:
        with open(filename, encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if start_line <= i <= end_line:
                    lines[i] = line.rstrip("\n\r")
                if i > end_line:
                    break
    except (OSError, UnicodeDecodeError):
        pass
    return lines


def get_node_line(node: Node) -> Optional[int]:
    """Get the primary source line for a node."""
    if node.source_mapping and node.source_mapping.lines:
        return node.source_mapping.lines[0]
    return None


def build_annotation_note(operation: Binary, result_tag: RoundingTag) -> str:
    """Build annotation note for division operations."""
    if operation.type == BinaryType.DIVISION:
        if result_tag == RoundingTag.UP:
            return "ceiling pattern"
        return "floor division"
    return ""


def _create_annotated_function(
    function: FunctionContract,
    query_tag: Optional[RoundingTag] = None,
) -> AnnotatedFunction:
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
        query_tag=query_tag,
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

        if line_num is None or line_num not in annotated.lines:
            continue

        annotated_line = annotated.lines[line_num]
        if node.irs_ssa:
            for operation in node.irs_ssa:
                _process_operation(operation, domain, annotated_line, annotated)


def analyze_function_annotated(
    function: FunctionContract,
    interprocedural: Optional[RoundingInterproceduralAnalyzer] = None,
    query_tag: Optional[RoundingTag] = None,
) -> AnnotatedFunction:
    """Analyze a function and build annotated source view."""
    annotated = _create_annotated_function(function, query_tag)

    if interprocedural and query_tag:
        annotated.path_traces = interprocedural.get_trace(function, query_tag)

    _populate_source_lines(annotated)

    rounding_analysis = RoundingAnalysis(interprocedural=interprocedural)
    engine = Engine.new(rounding_analysis, function)
    engine.run_analysis()
    node_results: dict[Node, AnalysisState] = engine.result()

    annotated.inconsistencies = rounding_analysis.inconsistencies
    annotated.annotation_mismatches = rounding_analysis.annotation_mismatches

    _process_node_results(function, node_results, annotated)
    return annotated


def _process_operation(
    operation: Union[Binary, Assignment, InternalCall, HighLevelCall, LibraryCall, Return],
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
    annotated: AnnotatedFunction,
) -> None:
    """Process an operation and add annotations."""
    if isinstance(operation, Binary) and operation.lvalue:
        result_name = get_variable_name(operation.lvalue)
        result_tag = get_tag(domain, operation.lvalue)
        note = build_annotation_note(operation, result_tag)
        unknown_reason = (
            get_unknown_reason(domain, operation.lvalue, result_tag)
            if isinstance(operation.lvalue, Variable)
            else None
        )
        if unknown_reason:
            note = unknown_reason
        annotated_line.annotations.append(
            LineAnnotation(variable_name=result_name, tag=result_tag, note=note)
        )

    elif isinstance(operation, Assignment) and operation.lvalue:
        lvalue_name = get_variable_name(operation.lvalue)
        lvalue_tag = get_tag(domain, operation.lvalue)
        annotated_line.annotations.append(
            LineAnnotation(variable_name=lvalue_name, tag=lvalue_tag)
        )

    elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)) and operation.lvalue:
        result_name = get_variable_name(operation.lvalue)
        result_tag = get_tag(domain, operation.lvalue)
        func_name = _get_call_function_name(operation)
        note = f"from {func_name}()"
        annotated_line.annotations.append(
            LineAnnotation(variable_name=result_name, tag=result_tag, note=note)
        )

    elif isinstance(operation, Return):
        for return_value in operation.values:
            if return_value:
                var_name = get_variable_name(return_value)
                tag = get_tag(domain, return_value)
                annotated.return_tags[var_name] = tag
                annotated_line.annotations.append(
                    LineAnnotation(variable_name=var_name, tag=tag, is_return=True)
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
        file_header = Text()
        location = f"[{relative_path}:{annotated.start_line}:{annotated.end_line}]"
        file_header.append(location, style="dim")
        console.print(file_header)

    line_width = len(str(annotated.end_line))

    for line_num in range(annotated.start_line, annotated.end_line + 1):
        if line_num not in annotated.lines:
            continue

        annotated_line = annotated.lines[line_num]
        _display_source_line(annotated_line, line_width)
        _display_annotations(annotated_line, line_width)

    _display_return_summary(annotated)
    _display_path_traces(annotated)
    _display_issues(annotated)
    console.print()


def _get_relative_path(filename: str) -> str:
    """Get a shorter relative path for display."""
    path = Path(filename)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        # If not relative to cwd, try to show just the last 2 components
        parts = path.parts
        if len(parts) >= 2:
            return str(Path(*parts[-2:]))
        return path.name


def _display_source_line(annotated_line: AnnotatedLine, line_width: int) -> None:
    """Display a single source line with line number."""
    line_num = annotated_line.line_number
    source = annotated_line.source_text

    line_num_str = str(line_num).rjust(line_width)
    entry_marker = "[bold magenta]→[/bold magenta]" if annotated_line.is_entry else " "

    console.print(f"{line_num_str} {entry_marker} │ {source}")


def _display_annotations(annotated_line: AnnotatedLine, line_width: int) -> None:
    """Display annotations below a source line."""
    if not annotated_line.annotations:
        return

    padding = " " * line_width
    seen_vars: set = set()

    for annotation in annotated_line.annotations:
        if annotation.variable_name in seen_vars:
            continue
        seen_vars.add(annotation.variable_name)

        prefix = "returns:" if annotation.is_return else ""
        var_display = f'"{annotation.variable_name}"'

        tag_text = format_tag_inline(annotation.tag)
        note_text = f" ({annotation.note})" if annotation.note else ""

        line = Text()
        line.append(f"{padding}   │     └── ", style="dim")
        if prefix:
            line.append(f"{prefix} ", style="bold")
        line.append(var_display, style="cyan")
        line.append(" → ")
        line.append(tag_text)
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
    for var_name, tag in annotated.return_tags.items():
        item = Text()
        item.append(var_name, style="cyan")
        item.append(" → ")
        item.append(format_tag_inline(tag))
        items.append(item)

    for i, item in enumerate(items):
        if i > 0:
            returns_line.append(", ")
        returns_line.append(item)

    console.print(returns_line)


def _display_path_traces(annotated: AnnotatedFunction) -> None:
    """Display interprocedural path traces for the queried tag."""
    if not annotated.path_traces or not annotated.query_tag:
        return

    console.print()
    header = Text()
    header.append("Path to ", style="bold")
    header.append(format_tag_inline(annotated.query_tag))
    header.append(":", style="bold")
    console.print(header)

    for trace_line in annotated.path_traces:
        console.print(f"  [dim]{trace_line}[/dim]")


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
            for var_name, tag in func.return_tags.items():
                line = Text()
                line.append(f"  {func_name}", style="bold")
                line.append(f" returns {var_name} → ")
                line.append(format_tag_inline(tag))
                console.print(line)
        else:
            console.print(f"  [bold]{func_name}[/bold] [dim](no return)[/dim]")


def display_function_results(
    results: dict[str, RoundingResult],
    query_tag: Optional[RoundingTag] = None,
    analyzer: Optional[RoundingInterproceduralAnalyzer] = None,
    functions: Optional[dict[str, FunctionContract]] = None,
) -> None:
    """Display interprocedural analysis results with optional traces."""
    console.print()
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    if query_tag:
        console.print(f"[bold]INTERPROCEDURAL ANALYSIS: canRound(*, {query_tag.name})[/bold]")
    else:
        console.print("[bold]INTERPROCEDURAL ANALYSIS: Function Results[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()

    for func_name, result in sorted(results.items()):
        line = Text()
        line.append(f"  {func_name}", style="bold")
        line.append(": ")
        line.append(format_tags_set(result.possible_tags))

        if query_tag:
            can_round = query_tag in result.possible_tags
            if can_round:
                line.append("  ")
                line.append("✓", style="bold green")
            else:
                line.append("  ")
                line.append("✗", style="bold red")

        console.print(line)

        # Show trace for matching functions when query tag is provided
        if query_tag and can_round and analyzer and functions:
            func = functions.get(func_name)
            if func:
                trace_lines = analyzer.get_trace(func, query_tag, indent=2)
                for trace_line in trace_lines:
                    console.print(f"[dim]{trace_line}[/dim]")

    console.print()


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Rounding direction analysis visualization tool"
    )
    parser.add_argument("project_path", help="Path to Solidity file or project directory")
    parser.add_argument(
        "-c", "--contract",
        help="Filter to contracts in this file (e.g., MockLinearMath.sol)"
    )
    parser.add_argument("-f", "--function", help="Filter to this specific function name")
    parser.add_argument(
        "-i", "--interprocedural", action="store_true",
        help="Enable interprocedural analysis"
    )
    parser.add_argument(
        "--query-tag", choices=["UP", "DOWN", "NEUTRAL", "UNKNOWN"],
        help="Query if functions can produce this tag"
    )
    parser.add_argument(
        "--show-summaries", action="store_true",
        help="Display function summaries (implies -i)"
    )
    return parser


def _collect_functions(
    slither: Slither,
    contract_filter: Optional[str],
    function_filter: Optional[str],
) -> list[FunctionContract]:
    """Collect functions to analyze based on filters."""
    functions: list[FunctionContract] = []
    for contract in slither.contracts:
        if contract_filter:
            contract_file = (
                contract.source_mapping.filename.short if contract.source_mapping else ""
            )
            if contract_filter not in contract_file:
                continue

        for function in contract.functions:
            if function_filter and function.name != function_filter:
                continue
            if isinstance(function, FunctionContract) and function.is_implemented:
                functions.append(function)
    return functions


def _run_interprocedural_analysis(
    functions: list[FunctionContract],
) -> tuple[RoundingInterproceduralAnalyzer, dict[str, RoundingResult], dict[str, FunctionContract]]:
    """Run interprocedural analysis on functions."""
    base_analysis = RoundingAnalysis()
    analyzer = RoundingInterproceduralAnalyzer(base_analysis)
    results: dict[str, RoundingResult] = {}
    functions_by_label: dict[str, FunctionContract] = {}

    for function in functions:
        contract_name = function.contract.name if function.contract else "Unknown"
        function_label = f"{contract_name}.{function.name}"
        try:
            results[function_label] = analyzer.analyze_call(function)
            functions_by_label[function_label] = function
        except Exception as exception:
            console.print(f"[red]Error analyzing {function_label}:[/red] {exception}")

    return analyzer, results, functions_by_label


def _analyze_with_query_tag(
    functions: list[FunctionContract],
    analyzer: RoundingInterproceduralAnalyzer,
    results: dict[str, RoundingResult],
    query_tag: RoundingTag,
) -> None:
    """Analyze and display functions matching a query tag."""
    function_analyses: list[AnnotatedFunction] = []
    for function in functions:
        try:
            analysis = analyze_function_annotated(function, analyzer, query_tag)
            contract_name = function.contract.name if function.contract else "Unknown"
            function_label = f"{contract_name}.{function.name}"
            if function_label in results and query_tag in results[function_label].possible_tags:
                function_analyses.append(analysis)
        except Exception as exception:
            console.print(f"[red]Error analyzing {function.name}:[/red] {exception}")

    for analysis in function_analyses:
        display_annotated_source(analysis)


def _run_basic_analysis(functions: list[FunctionContract]) -> None:
    """Run basic intraprocedural analysis and display results."""
    function_analyses: list[AnnotatedFunction] = []
    for function in functions:
        try:
            function_analyses.append(analyze_function_annotated(function))
        except Exception as exception:
            console.print(f"[red]Error analyzing {function.name}:[/red] {exception}")

    if not function_analyses:
        console.print("[yellow]No functions found to analyze[/yellow]")
        return

    for analysis in function_analyses:
        display_annotated_source(analysis)

    if len(function_analyses) > 1:
        display_summary_table(function_analyses)


def main() -> None:
    """Main entry point."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        console.print(f"[red]Error:[/red] Path not found: {project_path}")
        sys.exit(1)

    slither = Slither(str(project_path))
    functions = _collect_functions(slither, args.contract, args.function)

    if not functions:
        console.print("[yellow]No functions found to analyze[/yellow]")
        return

    use_interprocedural = args.interprocedural or args.show_summaries or args.query_tag

    if not use_interprocedural:
        _run_basic_analysis(functions)
        return

    analyzer, results, functions_by_label = _run_interprocedural_analysis(functions)

    query_tag: Optional[RoundingTag] = None
    if args.query_tag:
        query_tag = RoundingTag[args.query_tag]

    if args.show_summaries:
        display_function_results(results, query_tag, analyzer, functions_by_label)

    if query_tag:
        _analyze_with_query_tag(functions, analyzer, results, query_tag)
    elif not args.show_summaries:
        _run_basic_analysis(functions)


if __name__ == "__main__":
    main()
