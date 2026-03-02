"""Build annotated source views from rounding analysis results."""

from __future__ import annotations


from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
    RoundingAnalysis,
)
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.core.models import (
    AnnotatedFunction,
    AnnotatedLine,
    LineAnnotation,
    get_node_line,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    KnownLibraryTags,
)
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.variable import Variable
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.unpack import Unpack
from slither.slithir.utils.utils import RVALUE

_logger = get_logger()


def analyze_function(
    function: FunctionContract,
    show_all: bool = False,
    known_tags: KnownLibraryTags | None = None,
) -> AnnotatedFunction:
    """Analyze a function and build annotated source view."""
    annotated = _create_annotated_function(function)
    _populate_source_lines(annotated)

    analysis = RoundingAnalysis(known_tags=known_tags)
    engine = Engine.new(analysis, function)
    engine.run_analysis()
    node_results: dict[Node, AnalysisState] = engine.result()

    annotated.inconsistencies = analysis.inconsistencies
    annotated.annotation_mismatches = analysis.annotation_mismatches
    annotated.node_results = node_results

    _process_node_results(function, node_results, annotated, show_all=show_all)
    annotated.traces = extract_variable_traces(annotated)
    return annotated


# ── Trace extraction ─────────────────────────────────────────────


def extract_variable_traces(
    annotated: AnnotatedFunction,
) -> dict[str, TraceNode]:
    """Extract all variable traces from analysis results.

    Walks node_results, collects traces via the public
    domain.state.get_trace() method, and deduplicates by trace
    identity — preferring named variables over TMPs when they share
    the same TraceNode (via assignment).

    Args:
        annotated: An AnnotatedFunction with populated node_results.

    Returns:
        Dict mapping variable name to its provenance TraceNode.
    """
    seen_traces: dict[int, tuple[str, TraceNode]] = {}

    for node, analysis_state in annotated.node_results.items():
        if analysis_state.post.variant != DomainVariant.STATE:
            continue

        domain = analysis_state.post
        if not node.irs_ssa:
            continue

        for operation in node.irs_ssa:
            variable = _get_lvalue(operation)
            if variable is None:
                continue

            trace = domain.state.get_trace(variable)
            if trace is None:
                continue

            trace_id = id(trace)
            existing = seen_traces.get(trace_id)
            if existing is None or existing[0].startswith("TMP"):
                seen_traces[trace_id] = (variable.name, trace)

    return {name: trace for name, trace in seen_traces.values()}


def _get_lvalue(operation: Operation) -> Variable | None:
    """Get lvalue from an operation if it produces a Variable."""
    if not isinstance(operation, OperationWithLValue):
        return None
    lvalue = operation.lvalue
    if isinstance(lvalue, Variable):
        return lvalue
    return None


# ── Helpers ──────────────────────────────────────────────────────


def _get_variable_name(
    variable: RVALUE | Variable | None,
) -> str:
    """Get variable name, or string representation."""
    if isinstance(variable, Variable):
        return variable.name
    return str(variable) if variable else "?"


def _get_tags(
    domain: RoundingDomain,
    variable: RVALUE | Variable | None,
) -> TagSet:
    """Get rounding tags for a variable."""
    if isinstance(variable, Variable):
        return domain.state.get_tags(variable)
    return frozenset({RoundingTag.NEUTRAL})


def _get_unknown_reason(
    domain: RoundingDomain,
    variable: Variable,
    tags: TagSet,
) -> str | None:
    """Get unknown reason if tags include UNKNOWN."""
    if RoundingTag.UNKNOWN in tags:
        return domain.state.get_unknown_reason(variable)
    return None


def _read_source_lines(
    filename: str,
    start_line: int,
    end_line: int,
) -> dict[int, str]:
    """Read source file lines within the given range."""
    lines: dict[int, str] = {}
    try:
        with open(filename, encoding="utf-8") as source_file:
            for line_index, line in enumerate(source_file, start=1):
                if start_line <= line_index <= end_line:
                    lines[line_index] = line.rstrip("\n\r")
                if line_index > end_line:
                    break
    except (OSError, UnicodeDecodeError) as exc:
        _logger.warning(
            "Could not read source file {filename}: {exc}",
            filename=filename,
            exc=exc,
        )
    return lines


def _build_division_note(
    operation: Binary,
    result_tags: TagSet,
) -> str:
    """Build annotation note for division operations."""
    if operation.type != BinaryType.DIVISION:
        return ""
    if result_tags == frozenset({RoundingTag.UP}):
        return "ceiling pattern"
    if result_tags == frozenset({RoundingTag.DOWN}):
        return "floor division"
    return ""


# ── Annotated function construction ─────────────────────────────


def _create_annotated_function(
    function: FunctionContract,
) -> AnnotatedFunction:
    """Create initial AnnotatedFunction from function metadata."""
    source_mapping = function.source_mapping
    filename = source_mapping.filename.absolute if source_mapping else ""
    start_line = (
        source_mapping.lines[0] if source_mapping and source_mapping.lines else 0
    )
    end_line = (
        source_mapping.lines[-1] if source_mapping and source_mapping.lines else 0
    )

    return AnnotatedFunction(
        function_name=function.name,
        contract_name=(function.contract.name if function.contract else "Unknown"),
        filename=filename,
        start_line=start_line,
        end_line=end_line,
    )


def _populate_source_lines(
    annotated: AnnotatedFunction,
) -> None:
    """Populate annotated function with source lines."""
    source_lines = _read_source_lines(
        annotated.filename, annotated.start_line, annotated.end_line
    )
    for line_num, text in source_lines.items():
        annotated.lines[line_num] = AnnotatedLine(
            line_number=line_num,
            source_text=text,
        )


# ── Node / operation processing ─────────────────────────────────


def _process_node_results(
    function: FunctionContract,
    node_results: dict[Node, AnalysisState],
    annotated: AnnotatedFunction,
    *,
    show_all: bool = False,
) -> None:
    """Process analysis results and add annotations to lines."""
    for node in function.nodes:
        if node not in node_results:
            continue
        post = node_results[node].post
        if post.variant != DomainVariant.STATE:
            continue

        line_num = get_node_line(node)
        _maybe_mark_entry(
            node,
            line_num,
            post,
            function,
            annotated,
            show_all=show_all,
        )

        if line_num is None or line_num not in annotated.lines:
            continue
        if not node.irs_ssa:
            continue

        annotated_line = annotated.lines[line_num]
        for operation in node.irs_ssa:
            _process_operation(
                operation,
                post,
                annotated_line,
                annotated,
            )


def _maybe_mark_entry(
    node: Node,
    line_num: int | None,
    domain: RoundingDomain,
    function: FunctionContract,
    annotated: AnnotatedFunction,
    *,
    show_all: bool,
) -> None:
    """Mark entry point and optionally add parameter annotations."""
    if node.type != NodeType.ENTRYPOINT:
        return
    if not line_num or line_num not in annotated.lines:
        return
    annotated.lines[line_num].is_entry = True
    if not show_all:
        return
    for parameter in function.parameters:
        tags = _get_tags(domain, parameter)
        annotated.lines[line_num].annotations.append(
            LineAnnotation(
                variable_name=parameter.name,
                tags=tags,
                note="parameter",
            )
        )


def _process_operation(
    operation: (
        Binary
        | Assignment
        | InternalCall
        | HighLevelCall
        | LibraryCall
        | Return
        | Unpack
    ),
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
    annotated: AnnotatedFunction,
) -> None:
    """Process an operation and add annotations."""
    if isinstance(operation, Binary) and operation.lvalue:
        _process_binary(operation, domain, annotated_line)
    elif isinstance(operation, Assignment) and operation.lvalue:
        _process_assignment(operation, domain, annotated_line)
    elif (
        isinstance(
            operation,
            (InternalCall, HighLevelCall, LibraryCall),
        )
        and operation.lvalue
    ):
        _process_call(operation, domain, annotated_line)
    elif isinstance(operation, Unpack) and operation.lvalue:
        _process_unpack(operation, domain, annotated_line)
    elif isinstance(operation, Return):
        _process_return(
            operation,
            domain,
            annotated_line,
            annotated,
        )


def _process_binary(
    operation: Binary,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process binary operation."""
    result_name = _get_variable_name(operation.lvalue)
    result_tags = _get_tags(domain, operation.lvalue)

    if isinstance(operation.lvalue, Variable):
        unknown = _get_unknown_reason(
            domain,
            operation.lvalue,
            result_tags,
        )
        note = unknown or _build_binary_reasoning(
            operation,
            domain,
            result_tags,
        )
    else:
        note = _build_division_note(operation, result_tags)

    annotated_line.annotations.append(
        LineAnnotation(
            variable_name=result_name,
            tags=result_tags,
            note=note,
        )
    )


def _build_binary_reasoning(
    operation: Binary,
    domain: RoundingDomain,
    result_tags: TagSet,
) -> str:
    """Build reasoning note showing operand tags."""
    left_tags = _get_tags(domain, operation.variable_left)
    right_tags = _get_tags(domain, operation.variable_right)
    left_name = _get_variable_name(operation.variable_left)
    right_name = _get_variable_name(operation.variable_right)

    op_symbol = _get_operation_symbol(operation.type)
    base_note = _build_division_note(operation, result_tags)

    left_str = _format_tagset(left_tags)
    right_str = _format_tagset(right_tags)
    reasoning = f"{left_name}:{left_str} {op_symbol} {right_name}:{right_str}"
    if base_note:
        return f"{reasoning} ({base_note})"
    return reasoning


def _format_tagset(tags: TagSet) -> str:
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


def _process_assignment(
    operation: Assignment,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process assignment operation."""
    lvalue_name = _get_variable_name(operation.lvalue)
    lvalue_tags = _get_tags(domain, operation.lvalue)
    annotated_line.annotations.append(
        LineAnnotation(variable_name=lvalue_name, tags=lvalue_tags)
    )


def _process_unpack(
    operation: Unpack,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process unpack operation."""
    lvalue_name = _get_variable_name(operation.lvalue)
    lvalue_tags = _get_tags(domain, operation.lvalue)
    tuple_name = operation.tuple.name
    note = f"{tuple_name}[{operation.index}]"
    annotated_line.annotations.append(
        LineAnnotation(
            variable_name=lvalue_name,
            tags=lvalue_tags,
            note=note,
        )
    )


def _process_call(
    operation: InternalCall | HighLevelCall | LibraryCall,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
) -> None:
    """Process call operation."""
    result_name = _get_variable_name(operation.lvalue)
    result_tags = _get_tags(domain, operation.lvalue)
    func_name = _get_call_function_name(operation)
    note = f"from {func_name}()"
    annotated_line.annotations.append(
        LineAnnotation(
            variable_name=result_name,
            tags=result_tags,
            note=note,
        )
    )


def _process_return(
    operation: Return,
    domain: RoundingDomain,
    annotated_line: AnnotatedLine,
    annotated: AnnotatedFunction,
) -> None:
    """Process return operation."""
    for return_value in operation.values:
        if not return_value:
            continue
        var_name = _get_variable_name(return_value)
        tags = _get_tags(domain, return_value)
        existing = annotated.return_tags.get(var_name, frozenset())
        annotated.return_tags[var_name] = existing | tags
        annotated_line.annotations.append(
            LineAnnotation(
                variable_name=var_name,
                tags=tags,
                is_return=True,
            )
        )


def _get_call_function_name(
    operation: InternalCall | HighLevelCall | LibraryCall,
) -> str:
    """Extract function name from call operation."""
    if isinstance(operation, InternalCall):
        if operation.function:
            return operation.function.name
        return str(operation.function_name)
    return str(operation.function_name.value)
