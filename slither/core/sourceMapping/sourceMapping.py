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
        return {'start':s, 'length':l, 'filename': filename}

    def set_offset(self, offset, slither):
        self._source_mapping = self._convert_source_mapping(offset, slither)

