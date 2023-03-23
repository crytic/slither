import re
from abc import ABCMeta
from typing import Dict, Union, List, Tuple, TYPE_CHECKING, Optional, Any

from Crypto.Hash import SHA1
from crytic_compile.utils.naming import Filename
from slither.core.context.context import Context

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit


# We split the source mapping into two objects
# The reasoning is to allow any object to just inherit from SourceMapping
# To have then everything accessible through obj.source_mapping._
# All an object needs to do is to inherits from SourceMapping
# And call set_offset at some point

# pylint: disable=too-many-instance-attributes
class Source:
    def __init__(self, compilation_unit: "SlitherCompilationUnit") -> None:
        self.start: int = 0
        self.length: int = 0
        self.filename: Filename = Filename("", "", "", "")
        self.is_dependency: bool = False
        self.lines: List[int] = []
        self.starting_column: int = 0
        self.ending_column: int = 0
        self.end: int = 0
        self.compilation_unit = compilation_unit

    def to_json(self) -> Dict:
        return {
            "start": self.start,
            "length": self.length,
            # TODO investigate filename_used usecase
            # It creates non-deterministic result
            # As it sometimes refer to the relative and sometimes to the absolute
            # "filename_used": self.filename.used,
            "filename_relative": self.filename.relative,
            "filename_absolute": self.filename.absolute,
            "filename_short": self.filename.short,
            "is_dependency": self.is_dependency,
            "lines": self.lines,
            "starting_column": self.starting_column,
            "ending_column": self.ending_column,
        }

    def to_markdown(self, markdown_root: str) -> str:
        lines = self._get_lines_str(line_descr="L")
        filename_relative: str = self.filename.relative if self.filename.relative else ""
        return f"{markdown_root}{filename_relative}{lines}"

    def to_detailed_str(self) -> str:
        lines = self._get_lines_str()
        filename_short: str = self.filename.short if self.filename.short else ""
        return f"{filename_short}{lines} ({self.starting_column} - {self.ending_column})"

    def _get_lines_str(self, line_descr: str = "") -> str:

        line_prefix = self.compilation_unit.core.line_prefix

        lines = self.lines
        if not lines:
            return ""
        if len(lines) == 1:
            return f"{line_prefix}{line_descr}{lines[0]}"

        return f"{line_prefix}{line_descr}{lines[0]}-{line_descr}{lines[-1]}"

    @property
    def content(self) -> str:
        """
        Return the txt content of the Source

        Returns:

        """
        # If the compilation unit was not initialized, it means that the set_offset was never called
        # on the corresponding object, which should not happen
        assert self.compilation_unit
        return self.compilation_unit.core.source_code[self.filename.absolute][self.start : self.end]

    @property
    def content_hash(self) -> str:
        """
        Return sha1(self.content)

        Returns:

        """
        h = SHA1.new()
        h.update(self.content.encode("utf8"))
        return h.hexdigest()

    def __str__(self) -> str:
        lines = self._get_lines_str()
        filename_short: str = self.filename.short if self.filename.short else ""
        return f"{filename_short}{lines}"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.start == other.start
            and self.length == other.length
            and self.filename == other.filename
            and self.is_dependency == other.is_dependency
            and self.lines == other.lines
            and self.starting_column == other.starting_column
            and self.ending_column == other.ending_column
            and self.end == other.end
        )


def _compute_line(
    compilation_unit: "SlitherCompilationUnit", filename: Filename, start: int, length: int
) -> Tuple[List[int], int, int]:
    """
    Compute line(s) numbers and starting/ending columns
    from a start/end offset. All numbers start from 1.

    Not done in an efficient way
    """

    start_line, starting_column = compilation_unit.core.crytic_compile.get_line_from_offset(
        filename, start
    )
    end_line, ending_column = compilation_unit.core.crytic_compile.get_line_from_offset(
        filename, start + length
    )
    return list(range(start_line, end_line + 1)), starting_column, ending_column


def _convert_source_mapping(
    offset: str, compilation_unit: "SlitherCompilationUnit"
) -> Source:  # pylint: disable=too-many-locals
    """
    Convert a text offset to a real offset
    see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings
    Returns:
        (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
    """
    sourceUnits = compilation_unit.source_units

    position = re.findall("([0-9]*):([0-9]*):([-]?[0-9]*)", offset)
    if len(position) != 1:
        return Source(compilation_unit)

    s, l, f = position[0]
    s = int(s)
    l = int(l)
    f = int(f)

    if f not in sourceUnits:
        new_source = Source(compilation_unit)
        new_source.start = s
        new_source.length = l
        return new_source
    filename_used = sourceUnits[f]

    # If possible, convert the filename to its absolute/relative version
    assert compilation_unit.core.crytic_compile

    filename: Filename = compilation_unit.core.crytic_compile.filename_lookup(filename_used)
    is_dependency = compilation_unit.core.crytic_compile.is_dependency(filename.absolute)

    (lines, starting_column, ending_column) = _compute_line(compilation_unit, filename, s, l)

    new_source = Source(compilation_unit)
    new_source.start = s
    new_source.length = l
    new_source.filename = filename
    new_source.is_dependency = is_dependency
    new_source.lines = lines
    new_source.starting_column = starting_column
    new_source.ending_column = ending_column
    new_source.end = new_source.start + l

    return new_source


class SourceMapping(Context, metaclass=ABCMeta):
    def __init__(self) -> None:
        super().__init__()
        self.source_mapping: Optional[Source] = None
        self.references: List[Source] = []

    def set_offset(
        self, offset: Union["Source", str], compilation_unit: "SlitherCompilationUnit"
    ) -> None:
        assert compilation_unit
        if isinstance(offset, Source):
            self.source_mapping = offset
        else:
            self.source_mapping = _convert_source_mapping(offset, compilation_unit)
        self.source_mapping.compilation_unit = compilation_unit

    def add_reference_from_raw_source(
        self, offset: str, compilation_unit: "SlitherCompilationUnit"
    ) -> None:
        s = _convert_source_mapping(offset, compilation_unit)
        self.references.append(s)
