import re
from typing import Dict, Union, Optional

from slither.core.context.context import Context


class SourceMapping(Context):
    def __init__(self):
        super().__init__()
        # TODO create a namedtuple for the source mapping rather than a dict
        self._source_mapping: Optional[Dict] = None

    @property
    def source_mapping(self) -> Optional[Dict]:
        return self._source_mapping

    @staticmethod
    def _compute_line(source_code, start, length):
        """
        Compute line(s) numbers and starting/ending columns
        from a start/end offset. All numbers start from 1.

        Not done in an efficient way
        """
        source_code = source_code.encode("utf-8")
        total_length = len(source_code)
        source_code = source_code.splitlines(True)
        counter = 0
        i = 0
        lines = []
        starting_column = None
        ending_column = None
        while counter < total_length:
            # Determine the length of the line, and advance the line number
            line_content = source_code[i]
            line_length = len(line_content)
            i = i + 1

            # Determine our column numbers.
            if starting_column is None and counter + line_length > start:
                starting_column = (start - counter) + 1
            if (
                starting_column is not None
                and ending_column is None
                and counter + line_length > start + length
            ):
                ending_column = ((start + length) - counter) + 1

            # Advance the current position counter, and determine line numbers.
            counter += line_length
            if counter > start:
                lines.append(i)

            # If our advanced position for the next line is out of range, stop.
            if counter > start + length:
                break

        return lines, starting_column, ending_column

    @staticmethod
    def _convert_source_mapping(offset: str, slither):  # pylint: disable=too-many-locals
        """
        Convert a text offset to a real offset
        see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings
        Returns:
            (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
        """
        sourceUnits = slither.source_units

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

        lines = []

        # If possible, convert the filename to its absolute/relative version
        if slither.crytic_compile:
            filenames = slither.crytic_compile.filename_lookup(filename_used)
            filename_absolute = filenames.absolute
            filename_relative = filenames.relative
            filename_short = filenames.short

            is_dependency = slither.crytic_compile.is_dependency(filename_absolute)

            if (
                filename_absolute in slither.source_code
                or filename_absolute in slither.crytic_compile.src_content
            ):
                filename = filename_absolute
            elif filename_relative in slither.source_code:
                filename = filename_relative
            elif filename_short in slither.source_code:
                filename = filename_short
            else:
                filename = filename_used
        else:
            filename = filename_used

        if slither.crytic_compile and filename in slither.crytic_compile.src_content:
            source_code = slither.crytic_compile.src_content[filename]
            (lines, starting_column, ending_column) = SourceMapping._compute_line(source_code, s, l)
        elif filename in slither.source_code:
            source_code = slither.source_code[filename]
            (lines, starting_column, ending_column) = SourceMapping._compute_line(source_code, s, l)
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

    def set_offset(self, offset: Union[Dict, str], slither):
        if isinstance(offset, dict):
            self._source_mapping = offset
        else:
            self._source_mapping = self._convert_source_mapping(offset, slither)

    def _get_lines_str(self, line_descr=""):
        lines = self.source_mapping.get("lines", None)
        if not lines:
            lines = ""
        elif len(lines) == 1:
            lines = "#{}{}".format(line_descr, lines[0])
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
