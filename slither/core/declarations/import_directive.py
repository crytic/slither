from slither.core.source_mapping.source_mapping import SourceMapping


class Import(SourceMapping):
    def __init__(self, filename: str):
        super().__init__()
        self._filename = filename

    @property
    def filename(self) -> str:
        return self._filename

    def __str__(self):
        return self.filename
