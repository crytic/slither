"""Data models for annotated source code display.

This module provides dataclasses for representing source code with inline
annotations showing variable ranges from data flow analysis.
"""

from dataclasses import dataclass, field


@dataclass
class LineAnnotation:
    """Annotation for a single variable on a source line.

    Attributes:
        variable_name: The name of the annotated variable.
        range_min: Formatted minimum value string.
        range_max: Formatted maximum value string.
        constraints: Additional constraints like "&& != 0".
        is_return: Whether this is a return value annotation.
        column: Column position for alignment (0-indexed).
        can_overflow: Whether this value can overflow (unchecked arithmetic).
        can_underflow: Whether this value can underflow (unchecked arithmetic).
    """

    variable_name: str
    range_min: str
    range_max: str
    constraints: str = ""
    is_return: bool = False
    column: int = 0
    can_overflow: bool = False
    can_underflow: bool = False


@dataclass
class AnnotatedLine:
    """Source line with its annotations.

    Attributes:
        line_number: 1-indexed line number in the source file.
        source_text: The raw source text for this line.
        annotations: List of variable annotations for this line.
        is_entry: Whether this is the function entry line.
        is_exit: Whether this is the function exit line.
    """

    line_number: int
    source_text: str
    annotations: list[LineAnnotation] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False


@dataclass
class FunctionBounds:
    """Constraints header for a function.

    Attributes:
        signature: Function signature string (e.g., "hmmm(uint256, uint256)").
        constraints: List of constraint strings (e.g., "(a <= (2**256 - 1) / b) == true").
    """

    signature: str
    constraints: list[str]


@dataclass
class AnnotatedFunction:
    """Complete annotated source view for a function.

    Attributes:
        function_name: Name of the analyzed function.
        contract_name: Name of the containing contract.
        filename: Path to the source file.
        start_line: First line number of the function.
        end_line: Last line number of the function.
        lines: Mapping from line number to AnnotatedLine.
        bounds: Optional bounds/constraints header.
    """

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    lines: dict[int, AnnotatedLine]
    bounds: FunctionBounds | None = None
