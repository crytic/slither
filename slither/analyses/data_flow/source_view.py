"""Annotated source code rendering for data flow analysis results.

This module provides functions to render source code with inline annotations
showing variable ranges in a tree-style format below each source line.
"""

from rich.console import Console

from slither.analyses.data_flow.analysis_models import (
    AnnotatedFunction,
    AnnotatedLine,
    FunctionBounds,
    LineAnnotation,
)

console = Console()

# Box drawing characters
BOX_TOP_LEFT = "\u250c"
BOX_VERTICAL = "\u2502"
BOX_CORNER = "\u2514"
BOX_HORIZONTAL = "\u2500"
ARROW = "\u2192"
ELEMENT_OF = "\u2208"


def render_annotated_function(func: AnnotatedFunction) -> None:
    """Render a complete annotated function view to the console."""
    if func.bounds:
        _render_bounds_header(func.bounds)
        console.print()

    _render_file_header(func.filename, func.start_line, func.end_line)
    console.print(BOX_VERTICAL)

    line_num_width = len(str(func.end_line))
    for line_num in range(func.start_line, func.end_line + 1):
        line = func.lines.get(line_num)
        if line:
            _render_source_line(line, line_num_width)
            _render_annotations(line)


def _render_bounds_header(bounds: FunctionBounds) -> None:
    """Render the constraints/bounds header section."""
    console.print(
        f"[bold]Bounds:[/bold] Bounds for subcontext: {bounds.signature} where:"
    )
    for i, constraint in enumerate(bounds.constraints, 1):
        console.print(f"  {i}. {constraint}")


def _render_file_header(filename: str, start_line: int, end_line: int) -> None:
    """Render the file header with path and line range."""
    # Abbreviate path to show just the filename or relative path
    short_path = _abbreviate_path(filename)
    # Escape brackets for Rich markup
    header = f"{BOX_TOP_LEFT}{BOX_HORIZONTAL}\\[{short_path}:{start_line}:{end_line}]"
    console.print(f"[dim]{header}[/dim]")


def _abbreviate_path(path: str) -> str:
    """Abbreviate a file path for display."""
    if len(path) <= 40:
        return path
    parts = path.replace("\\", "/").split("/")
    if len(parts) <= 2:
        return path
    return "../" + "/".join(parts[-2:])


def _render_source_line(line: AnnotatedLine, width: int) -> None:
    """Render a single source line with line number and optional entry/exit marker."""
    line_num_str = str(line.line_number).rjust(width)

    if line.is_entry or line.is_exit:
        marker = f" {ARROW}"
        style = "bold cyan"
    else:
        marker = "  "
        style = "white"

    console.print(f"[{style}]{line_num_str}{marker}   {line.source_text}[/{style}]")


def _render_annotations(line: AnnotatedLine) -> None:
    """Render tree-style annotations below a source line."""
    if not line.annotations:
        return

    width = len(str(line.line_number))
    indent = " " * (width + 6)  # Match source line indentation

    for annotation in line.annotations:
        _render_single_annotation(annotation, indent)


def _escape_rich_markup(text: str) -> str:
    """Escape Rich markup characters in text."""
    return text.replace("[", "\\[")


def _render_single_annotation(annotation: LineAnnotation, indent: str) -> None:
    """Render a single annotation line with tree connector."""
    col_spaces = " " * annotation.column if annotation.column > 0 else ""

    # Escape brackets in variable name to prevent Rich markup interpretation
    var_name = _escape_rich_markup(annotation.variable_name)

    if annotation.is_return:
        label = f'returns: "{var_name}"'
    else:
        label = f'"{var_name}"'

    range_str = _format_range_display(annotation.range_min, annotation.range_max)
    constraint_str = f" {annotation.constraints}" if annotation.constraints else ""

    # Build overflow warning string
    overflow_str = _format_overflow_warning(annotation.can_overflow, annotation.can_underflow)

    color = _get_range_color(annotation.range_min, annotation.range_max)
    line_text = f"{indent}{col_spaces}{BOX_CORNER}{BOX_HORIZONTAL}{BOX_HORIZONTAL} {label} {range_str}{constraint_str}"

    if overflow_str:
        console.print(f"[{color}]{line_text}[/{color}] [{_OVERFLOW_COLOR}]{overflow_str}[/{_OVERFLOW_COLOR}]")
    else:
        console.print(f"[{color}]{line_text}[/{color}]")


_OVERFLOW_COLOR = "bold red"


def _format_overflow_warning(can_overflow: bool, can_underflow: bool) -> str:
    """Format overflow/underflow warning string."""
    if can_overflow and can_underflow:
        return "\\[overflow/underflow possible]"
    if can_overflow:
        return "\\[overflow possible]"
    if can_underflow:
        return "\\[underflow possible]"
    return ""


def _format_range_display(range_min: str, range_max: str) -> str:
    """Format a range for display using element-of notation."""
    return f"{ELEMENT_OF} [ {range_min}, {range_max} ]"


def _get_range_color(range_min: str, range_max: str) -> str:
    """Determine color based on range characteristics."""
    if "2**256" in range_max or "MAX" in range_max:
        return "yellow"
    if range_min == range_max:
        return "green"
    return "cyan"


def format_range_value(
    value: int, bit_width: int = 256, is_signed: bool = False, exact: bool = False
) -> str:
    """Format an integer value for display.

    Args:
        value: The integer value to format.
        bit_width: The bit width of the variable type.
        is_signed: Whether the value is signed.
        exact: If True, return exact decimal value without abbreviation.
    """
    # Exact mode - just return the decimal value
    if exact:
        return str(value)

    if bit_width <= 0:
        bit_width = 256

    type_max = (1 << bit_width) - 1

    if is_signed:
        signed_max = (1 << (bit_width - 1)) - 1
        signed_min = -(1 << (bit_width - 1))
        if value == signed_max:
            return f"2**{bit_width - 1} - 1"
        if value == signed_min:
            return f"-2**{bit_width - 1}"

    if value == type_max:
        return f"2**{bit_width} - 1"
    if value == 0:
        return "0"

    # Check for powers of 2
    if value > 0 and (value & (value - 1)) == 0:
        exp = value.bit_length() - 1
        if exp >= 8:
            return f"2**{exp}"

    # Check for powers of 2 minus 1
    if value > 0 and ((value + 1) & value) == 0:
        exp = (value + 1).bit_length() - 1
        if exp >= 8:
            return f"2**{exp} - 1"

    # Format large hex values with abbreviation
    if bit_width >= 160 and value > 0xFFFFFFFF:
        return _format_abbreviated_hex(value, bit_width)

    # Format addresses specially
    if bit_width == 160:
        return _format_address(value)

    return str(value)


def _format_abbreviated_hex(value: int, bit_width: int) -> str:
    """Format a large hex value with middle abbreviation."""
    hex_str = format(value, "x")
    expected_len = bit_width // 4

    if len(hex_str) < expected_len:
        hex_str = hex_str.zfill(expected_len)

    if len(hex_str) > 12:
        return f"0x{hex_str[:3]}...{hex_str[-3:]}"
    return f"0x{hex_str}"


def _format_address(value: int) -> str:
    """Format an Ethereum address value."""
    if value == 0:
        return "0x000...000"
    hex_str = format(value, "040x")
    return f"0x{hex_str[:3]}...{hex_str[-3:]}"


def format_constraint(constraint_str: str) -> str:
    """Format a constraint string for display."""
    result = constraint_str
    result = result.replace("!=", " != ")
    result = result.replace("==", " == ")
    result = result.replace("<=", " <= ")
    result = result.replace(">=", " >= ")
    return result


def build_annotation_from_range(
    var_name: str,
    min_val: int,
    max_val: int,
    bit_width: int = 256,
    is_signed: bool = False,
    column: int = 0,
    is_return: bool = False,
    extra_constraints: str = "",
    exact: bool = False,
    can_overflow: bool = False,
    can_underflow: bool = False,
) -> LineAnnotation:
    """Build a LineAnnotation from numeric range values."""
    return LineAnnotation(
        variable_name=var_name,
        range_min=format_range_value(min_val, bit_width, is_signed, exact),
        range_max=format_range_value(max_val, bit_width, is_signed, exact),
        constraints=extra_constraints,
        is_return=is_return,
        column=column,
        can_overflow=can_overflow,
        can_underflow=can_underflow,
    )
