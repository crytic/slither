import re
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
        source_code = source_code.split('\n')
        counter = 0
        i = 0
        lines = []
        while counter < total_length:
            counter += len(source_code[i]) +1
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
            print(f)
            print(sourceUnits)
            return {'start':s, 'length':l}
        filename = sourceUnits[f]

        lines = []

        if filename in slither.source_code:
            lines = SourceMapping._compute_line(slither.source_code[filename], s, l)

        return {'start':s, 'length':l, 'filename': filename, 'lines' : lines }

    def set_offset(self, offset, slither):
        if isinstance(offset, dict):
            self._source_mapping = offset
        else:
            self._source_mapping = self._convert_source_mapping(offset, slither)


    @property
    def source_mapping_str(self):
        lines = self.source_mapping['lines']
        if not lines:
            lines = ''
        elif len(lines) == 1:
            lines = '#{}'.format(lines[0])
        else:
            lines = '#{}-{}'.format(lines[0], lines[-1])
        return '{}{}'.format(self.source_mapping['filename'], lines)

