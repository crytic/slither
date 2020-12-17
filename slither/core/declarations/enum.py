from typing import List

from slither.core.source_mapping.source_mapping import SourceMapping


class Enum(SourceMapping):
    def __init__(self, name: str, canonical_name: str, values: List[str]):
        super().__init__()
        self._name = name
        self._canonical_name = canonical_name
        self._values = values

    @property
    def canonical_name(self) -> str:
        return self._canonical_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def values(self) -> List[str]:
        return self._values

    def __str__(self):
        return self.name
