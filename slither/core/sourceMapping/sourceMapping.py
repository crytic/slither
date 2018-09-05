from slither.core.context.context import Context

class SourceMapping(Context):

    def __init__(self):
        super(SourceMapping, self).__init__()
        self._source_mapping = None
        self._offset = None

    def set_source_mapping(self, source_mapping):
        self._source_mapping = source_mapping

    @property
    def source_mapping(self):
        return self._source_mapping

    def set_offset(self, offset):
        self._offset = offset
