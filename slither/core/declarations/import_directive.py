from slither.core.source_mapping.source_mapping import SourceMapping

class Import(SourceMapping):

    def __init__(self, filename):
        super(Import, self).__init__()
        self._fimename = filename

    @property
    def filename(self):
        return self._filename

    def __str__(self):
        return self.filename
