"""Rich console display for rounding analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.text import Text

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.models import (
    AnnotatedFunction,
    AnnotatedLine,
    LineAnnotation,
    get_node_line,
)
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.operation import Operation

try:
    from slither.analyses.data_flow.analyses.rounding.explain.explainer import (
        TraceExplainer,
        extract_source_for_path,
        serialize_trace_path,
        split_trace_paths,
    )
    from slither.analyses.data_flow.analyses.rounding.explain.signature import (
        TraceAnalysis,
    )

    EXPLAIN_AVAILABLE = True
except ImportError:
    EXPLAIN_AVAILABLE = False

console = Console()


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


def display_annotated_source(
    annotated: AnnotatedFunction,
) -> None:
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


def display_trace_section(
    annotated: AnnotatedFunction,
    trace_tag: RoundingTag,
    explainer: Optional[TraceExplainer] = None,
    function_lookup: Optional[dict[str, Function]] = None,
) -> None:
    """Display trace section for variables with the traced tag."""
    traced = _collect_traced_variables(annotated, trace_tag)
    if not traced:
        return

    console.print()
    console.print("=" * 80)
    console.print(f"[bold cyan]TRACE: {trace_tag.name} tag provenance[/bold cyan]")
    console.print("=" * 80)

    for variable_name, line_number, trace in traced:
        console.print()
        location = f"(line {line_number})" if line_number else ""
        console.print(f"[bold]{variable_name}[/bold] {location}:")
        _display_trace_tree(trace, indent=1, filter_tag=trace_tag)
        if explainer is not None and function_lookup is not None:
            _display_trace_conditions(
                trace,
                trace_tag,
                function_lookup,
                annotated,
                explainer,
            )


def display_summary_table(
    analyses: list[AnnotatedFunction],
) -> None:
    """Display summary of all analyzed functions."""
    console.print()
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]SUMMARY: All Functions[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()

    for func in analyses:
        func_name = f"{func.contract_name}.{func.function_name}"
        if not func.return_tags:
            console.print(f"  [bold]{func_name}[/bold] [dim](no return)[/dim]")
            continue
        for var_name, tags in func.return_tags.items():
            filtered_tags = _filter_neutral(tags)
            line = Text()
            line.append(f"  {func_name}", style="bold")
            line.append(f" returns {var_name} → ")
            line.append(format_tag_inline(filtered_tags))
            console.print(line)


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


def _display_source_line(
    annotated_line: AnnotatedLine,
    line_width: int,
) -> None:
    """Display a single source line with line number."""
    line_num_str = str(annotated_line.line_number).rjust(line_width)
    if annotated_line.is_entry:
        entry_marker = "[bold magenta]\u2192[/bold magenta]"
    else:
        entry_marker = " "
    console.print(f"{line_num_str} {entry_marker} \u2502 {annotated_line.source_text}")


def _display_annotations(
    annotated_line: AnnotatedLine,
    line_width: int,
) -> None:
    """Display annotations below a source line."""
    if not annotated_line.annotations:
        return

    padding = " " * line_width
    seen_vars: set[str] = set()

    for annotation in annotated_line.annotations:
        if annotation.variable_name in seen_vars:
            continue
        seen_vars.add(annotation.variable_name)
        _render_single_annotation(annotation, padding)


def _render_single_annotation(
    annotation: LineAnnotation,
    padding: str,
) -> None:
    """Render a single annotation line to console."""
    prefix = "returns:" if annotation.is_return else ""
    var_display = f'"{annotation.variable_name}"'
    note_text = f" ({annotation.note})" if annotation.note else ""

    line = Text()
    line.append(f"{padding}   \u2502     \u2514\u2500\u2500 ", style="dim")
    if prefix:
        line.append(f"{prefix} ", style="bold")
    line.append(var_display, style="cyan")
    line.append(" \u2192 ")
    line.append(format_tag_inline(annotation.tags))
    if note_text:
        line.append(note_text, style="dim")

    console.print(line)


def _display_return_summary(
    annotated: AnnotatedFunction,
) -> None:
    """Display return value summary."""
    if not annotated.return_tags:
        return

    console.print()
    returns_line = Text()
    returns_line.append("Return Values: ", style="bold")

    items = []
    for var_name, tags in annotated.return_tags.items():
        filtered_tags = _filter_neutral(tags)
        item = Text()
        item.append(var_name, style="cyan")
        item.append(" \u2192 ")
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
            console.print(f"  [red]\u2717[/red] {inconsistency}")

    if annotated.annotation_mismatches:
        console.print()
        console.print("[bold red]Annotation Mismatches:[/bold red]")
        for mismatch in annotated.annotation_mismatches:
            console.print(f"  [red]\u2717[/red] {mismatch}")


def _collect_traced_variables(
    annotated: AnnotatedFunction,
    trace_tag: RoundingTag,
) -> list[tuple[str, Optional[int], TraceNode]]:
    """Collect variables with traces containing the specified tag."""
    results: list[tuple[str, Optional[int], TraceNode]] = []

    for node, analysis_state in annotated.node_results.items():
        if analysis_state.post.variant != DomainVariant.STATE:
            continue

        domain = analysis_state.post
        line_number = get_node_line(node)

        if not node.irs_ssa:
            continue

        for operation in node.irs_ssa:
            variable = _get_operation_lvalue(operation)
            if variable is None:
                continue

            tags = domain.state.get_tags(variable)
            if trace_tag not in tags:
                continue

            trace = domain.state.get_trace(variable)
            if trace is None:
                continue

            if not _trace_contains_tag(trace, trace_tag):
                continue

            results.append((variable.name, line_number, trace))

    return results


def _get_operation_lvalue(
    operation: Operation,
) -> Variable | None:
    """Get lvalue from operation if it has one."""
    if not isinstance(operation, OperationWithLValue):
        return None
    lvalue = operation.lvalue
    if isinstance(lvalue, Variable):
        return lvalue
    return None


def _trace_contains_tag(
    trace: TraceNode,
    tag: RoundingTag,
) -> bool:
    """Check if a trace or its children contain the specified tag."""
    if tag in trace.tags:
        return True
    return any(_trace_contains_tag(child, tag) for child in trace.children)


def _display_trace_tree(
    trace: TraceNode,
    indent: int,
    filter_tag: RoundingTag,
) -> None:
    """Display a trace node and its children as a tree."""
    prefix = "  " * indent + "\u2514\u2500\u2500 "
    console.print(f"{prefix}{trace.source}")

    for child in trace.children:
        if _trace_contains_tag(child, filter_tag):
            _display_trace_tree(child, indent + 1, filter_tag)


def _display_trace_conditions(
    trace: TraceNode,
    trace_tag: RoundingTag,
    function_lookup: dict[str, Function],
    annotated: AnnotatedFunction,
    explainer: TraceExplainer,
) -> None:
    """Display LM-identified conditions for each trace path."""
    paths = split_trace_paths(trace, trace_tag)
    contract_context = f"{annotated.contract_name}.{annotated.function_name}"
    for path_index, path in enumerate(paths):
        trace_text = serialize_trace_path(path)
        source_text = extract_source_for_path(path, function_lookup)
        analysis: TraceAnalysis = explainer(
            trace_chain=trace_text,
            traced_tag=trace_tag.name,
            solidity_source=source_text,
            contract_context=contract_context,
        )
        leaf_name = path[-1].function_name
        console.print()
        console.print(
            f"  [bold green]Path {path_index + 1} (\u2192 {leaf_name}):[/bold green]"
        )
        _render_trace_steps(analysis)


def _render_trace_steps(analysis: TraceAnalysis) -> None:
    """Render the step-by-step trace flow."""
    if not analysis.steps:
        return
    console.print("  [bold green]Flow:[/bold green]")
    for index, step in enumerate(analysis.steps):
        step_number = index + 1
        console.print(f"  [bold]{step_number}. {step.function_name}[/bold]")
        console.print(f"     [dim]when:[/dim] {step.condition}")
        console.print(f"     [dim]in:[/dim]   {step.inputs}")
        console.print(f"     [dim]op:[/dim]   {step.operation}")
        if step.next_call != "returns":
            console.print(f"     [dim]\u2192[/dim]     {step.next_call}")


def _filter_neutral(tags: TagSet) -> TagSet:
    """Remove NEUTRAL from a tag set if other tags exist."""
    if len(tags) > 1 and RoundingTag.NEUTRAL in tags:
        return tags - {RoundingTag.NEUTRAL}
    return tags
