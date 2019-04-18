import re
import os
from slither.core.context.context import Context

class SourceMapping(Context):

    def __init__(self):
        super(SourceMapping, self).__init__()
        self._source_mapping = None

    @property
    def source_mapping(self):
        return self._source_mapping

    @staticmethod
    def _compute_line(source_code, start, length):
        """
            Compute line(s) numbers and starting/ending columns
            from a start/end offset. All results start from 0.

            Not done in an efficient way
        """
        total_length = len(source_code)
        source_code = source_code.splitlines(True)
        counter = 0
        i = 0
        lines = []
        starting_column = None
        ending_column = None
        while counter < total_length:
            # Determine the length of the line, and advance the line number
            lineLength = len(source_code[i])
            i = i + 1

            # Determine our column numbers.
            if starting_column is None and counter + lineLength > start:
                starting_column = (start - counter) + 1
            if starting_column is not None and ending_column is None and counter + lineLength > start + length:
                ending_column = ((start + length) - counter) + 1

            # Advance the current position counter, and determine line numbers.
            counter += lineLength
            if counter > start:
                lines.append(i)

            # If our advanced position for the next line is out of range, stop.
            if counter > start + length:
                break

        return (lines, starting_column, ending_column)

    @staticmethod
    def _convert_source_mapping(offset, slither):
        '''
        Convert a text offset to a real offset
        see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings
        Returns:
            (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
        '''
        sourceUnits = slither.source_units

        position = re.findall('([0-9]*):([0-9]*):([-]?[0-9]*)', offset)
        if len(position) != 1:
            return {}

        s, l, f = position[0]
        s = int(s)
        l = int(l)
        f = int(f)

        if f not in sourceUnits:
            return {'start':s, 'length':l}
        filename = sourceUnits[f]

        if filename in slither.source_code:
            (lines, starting_column, ending_column) = SourceMapping._compute_line(slither.source_code[filename], s, l)
        else:
            (lines, starting_column, ending_column) = ([], None, None)

        return {'start': s, 'length': l, 'filename': filename, 'lines': lines,
                'starting_column': starting_column, 'ending_column': ending_column}

    def set_offset(self, offset, slither):
        if isinstance(offset, dict):
            self._source_mapping = offset
        else:
            self._source_mapping = self._convert_source_mapping(offset, slither)


    @property
    def source_mapping_str(self):

        def relative_path(path):
            # Remove absolute path for printing
            # Truffle returns absolutePath
            splited_path = path.split(os.sep)
            if 'contracts' in splited_path:
                idx = splited_path.index('contracts')
                return os.sep.join(splited_path[idx-1:])
            return path

        lines = self.source_mapping['lines']
        if not lines:
            lines = ''
        elif len(lines) == 1:
            lines = '#{}'.format(lines[0])
        else:
            lines = '#{}-{}'.format(lines[0], lines[-1])
        return '{}{}'.format(relative_path(self.source_mapping['filename']), lines)

