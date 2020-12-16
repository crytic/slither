from typing import Optional

from slither.core.source_mapping.source_mapping import SourceMapping


class Import(SourceMapping):
    def __init__(self, filename: str):
        super().__init__()
        self._filename = filename
        self._alias: Optional[str] = None

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def alias(self) -> Optional[str]:
        return self._alias

    @alias.setter
    def alias(self, a: str):
        self._alias = a

    def __str__(self):
        return self.filename
