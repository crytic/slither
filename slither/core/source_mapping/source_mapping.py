import re
from typing import Dict, Union, Optional, List, Tuple, TYPE_CHECKING

from slither.core.context.context import Context

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit


class SourceMapping(Context):
    def __init__(self) -> None:
        super().__init__()
        # TODO create a namedtuple for the source mapping rather than a dict
        self._source_mapping: Optional[Dict] = None
        # self._start: Optional[int] = None
        # self._length: Optional[int] = None
        # self._filename_used: Optional[str] = None
        # self._filename_relative: Optional[str] = None
        # self._filename_absolute: Optional[str] = None
        # self._filename_short: Optional[str] = None
        # self._is_dependency: Optional[bool] = None
        # self._lines: Optional[List[int]] = None
        # self._starting_column: Optional[int] = None
        # self._ending_column: Optional[int] = None

    @property
    def source_mapping(self) -> Optional[Dict]:
        return self._source_mapping

    @staticmethod
    def _compute_line(
        compilation_unit: "SlitherCompilationUnit", filename, start: int, length: int
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
        self, offset: str, compilation_unit: "SlitherCompilationUnit"
    ):  # pylint: disable=too-many-locals
        """
        Convert a text offset to a real offset
        see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings
        Returns:
            (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
        """
        sourceUnits = compilation_unit.source_units

        position = re.findall("([0-9]*):([0-9]*):([-]?[0-9]*)", offset)
        if len(position) != 1:
            return {}

        s, l, f = position[0]
        s = int(s)
        l = int(l)
        f = int(f)

        if f not in sourceUnits:
            return {"start": s, "length": l}
        filename_used = sourceUnits[f]
        filename_absolute = None
        filename_relative = None
        filename_short = None

        is_dependency = False

        # If possible, convert the filename to its absolute/relative version
        if compilation_unit.core.crytic_compile:
            filenames = compilation_unit.core.crytic_compile.filename_lookup(filename_used)
            filename_absolute = filenames.absolute
            filename_relative = filenames.relative
            filename_short = filenames.short

            is_dependency = compilation_unit.core.crytic_compile.is_dependency(filename_absolute)

            if (
                filename_absolute in compilation_unit.core.source_code
                or filename_absolute in compilation_unit.core.crytic_compile.src_content
            ):
                filename = filename_absolute
            elif filename_relative in compilation_unit.core.source_code:
                filename = filename_relative
            elif filename_short in compilation_unit.core.source_code:
                filename = filename_short
            else:
                filename = filename_used
        else:
            filename = filename_used

        if compilation_unit.core.crytic_compile:
            (lines, starting_column, ending_column) = self._compute_line(
                compilation_unit, filename, s, l
            )
        else:
            (lines, starting_column, ending_column) = ([], None, None)

        return {
            "start": s,
            "length": l,
            "filename_used": filename_used,
            "filename_relative": filename_relative,
            "filename_absolute": filename_absolute,
            "filename_short": filename_short,
            "is_dependency": is_dependency,
            "lines": lines,
            "starting_column": starting_column,
            "ending_column": ending_column,
        }

    def set_offset(self, offset: Union[Dict, str], compilation_unit: "SlitherCompilationUnit"):
        if isinstance(offset, dict):
            self._source_mapping = offset
        else:
            self._source_mapping = self._convert_source_mapping(offset, compilation_unit)

    def _get_lines_str(self, line_descr=""):
        lines = self.source_mapping.get("lines", None)
        if not lines:
            lines = ""
        elif len(lines) == 1:
            lines = f"#{line_descr}{lines[0]}"
        else:
            lines = f"#{line_descr}{lines[0]}-{line_descr}{lines[-1]}"
        return lines

    def source_mapping_to_markdown(self, markdown_root: str) -> str:
        lines = self._get_lines_str(line_descr="L")
        return f'{markdown_root}{self.source_mapping.get("filename_relative", "")}{lines}'

    @property
    def source_mapping_str(self) -> str:
        lines = self._get_lines_str()
        return f'{self.source_mapping.get("filename_short", "")}{lines}'
