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
            Compute line(s) number from a start/end offset
            Not done in an efficient way
        """
        total_length = len(source_code)
        source_code = source_code.splitlines(True)
        counter = 0
        i = 0
        lines = []
        while counter < total_length:
            counter += len(source_code[i])
            i = i+1
            if counter > start:
                lines.append(i)
            if counter > start+length:
                break
        return lines

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
        filename_used = sourceUnits[f]
        filename_absolute = None
        filename_relative = None
        filename_short = None

        lines = []

        # If possible, convert the filename to its absolute/relative version
        if slither.crytic_compile:
            filenames = slither.crytic_compile.filename_lookup(filename_used)
            filename_absolute = filenames.absolute
            filename_relative = filenames.relative
            filename_short = filenames.short

            if filename_absolute in slither.source_code:
                filename = filename_absolute
            elif filename_relative in slither.source_code:
                filename = filename_relative
            elif filename_short in slither.source_code:
                filename = filename_short
            else:#
                filename = filename_used.used
        else:
            filename = filename_used

        if filename in slither.source_code:
            lines = SourceMapping._compute_line(slither.source_code[filename], s, l)

        return {'start':s,
                'length':l,
                'filename_used': filename_used,
                'filename_relative': filename_relative,
                'filename_absolute': filename_absolute,
                'filename_short': filename_short,
                'lines' : lines }

    def set_offset(self, offset, slither):
        if isinstance(offset, dict):
            self._source_mapping = offset
        else:
            self._source_mapping = self._convert_source_mapping(offset, slither)


    @property
    def source_mapping_str(self):

#        def relative_path(path):
#            # Remove absolute path for printing
#           # Truffle returns absolutePath
#           splited_path = path.split(os.sep)
#           if 'contracts' in splited_path:
#               idx = splited_path.index('contracts')
#               return os.sep.join(splited_path[idx-1:])
#           return path

        lines = self.source_mapping['lines']
        if not lines:
            lines = ''
        elif len(lines) == 1:
            lines = '#{}'.format(lines[0])
        else:
            lines = '#{}-{}'.format(lines[0], lines[-1])
        return '{}{}'.format(self.source_mapping['filename_short'], lines)

